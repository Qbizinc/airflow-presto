from airflow.hooks.presto_hook import PrestoHook
from airflow.models import BaseOperator
from airflow.utils.decorators import apply_defaults
from airflow import settings
from airflow.models import Connection
import boto3


class ECSOperator(BaseOperator):
    template_fields = ('cluster', 'count', 'group', 'launchType', 'referenceId', 'startedBy',
        'taskDefinition')
    template_ext = ('.sql', '.hql')  # Older versions of Airflow dont work with single element tuples
    @apply_defaults
    def __init__(
            self,
            cluster: str,
            count: int,
            group: str,
            launchType: str,
            networkConfiguration: dict,
            overrides: dict,
            referenceId: str,
            startedBy: str,
            taskDefinition: str,
            *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.cluster = cluster
        self.count = count
        self.group = group
        self.launchType = launchType
        self.networkConfiguration = networkConfiguration
        self.overrides = overrides
        self.referenceId = referenceId
        self.startedBy = startedBy
        self.taskDefinition = taskDefinition

    def create_single_node_task(self):
        raise NotImplementedError

    def register_connection(self, conn_id, conn_type, host, login, password, port):
        conn = Connection(
                conn_id=conn_id,
                conn_type=conn_type,
                host=host,
                login=login,
                password=password,
                port=port
        ) #create a connection object
        session = settings.Session() # get the session
        session.add(conn)
        session.commit() # it will insert the connection object programmatically.
        self.log.info(f"connection type {conn_type} registered for host {host} named {conn_id}")

    def unregister_connection(self, conn_id):
        raise NotImplementedError

    def query_presto(self, query, conn_id):
        self.log.info(f"Querying {conn_id}")
        ph = PrestoHook(presto_conn_id=conn_id)
        records = ph.get_records(query)
        self.log.info(f"Query complete,  {len(records)} records retrieved")
        return records

    def get_task_private_IP(self, task, cluster=self.cluster):
        self.log.info(f"Retrieving private IP address for task {task} on cluster {cluster}")
        client = boto3.client('ecs')
        describe_response = client.describe_tasks(cluster=cluster, tasks=[task])
        # Assuming only the one task,  this grabs the Private IP of the task
        for detail in describe_response['tasks'][0]['attachments'][0]['details']:
            if detail['name'] == 'privateIPv4Address':
                ip_address = detail['value']
                self.log.info(f"task {task} is ataddress {ip_address}")
                return ip_address
        self.log.error(f'''IP discovery did not execute correctly, client response:
            {describe_response}''')


    def stop_ecs_task(self):
        # TODO: first query the groups then take it all down
        raise NotImplementedError
        response = client.stop_task(
            cluster='string',
            task='string',
            reason='string'
        )
        return response


    def create_ecs_task(self, coordinator: bool):
        client = boto3.client('ecs')
        response = client.run_task(
            # capacityProviderStrategy=[
            #     {
            #         'capacityProvider': 'FARGATE',
            #         # 'weight': 123,
            #         # 'base': 123
            #     },
            # ],
            cluster=self.cluster,
            count=self.count,
            enableECSManagedTags=True, #True|False,
            group=self.group,
            launchType=self.launchType, #'EC2'|'FARGATE',
            networkConfiguration=self.networkConfiguration,
            overrides=self.overrides,
            # overrides={
            #     'containerOverrides': [
            #         {
            #             'name': 'string',
            #             'command': [
            #                 'string',
            #             ],
            #             'environment': [
            #                 {
            #                     'name': 'string',
            #                     'value': 'string'
            #                 },
            #             ],
            #             'environmentFiles': [
            #                 {
            #                     'value': 'string',
            #                     'type': 's3'
            #                 },
            #             ],
            #             'cpu': 123,
            #             'memory': 123,
            #             'memoryReservation': 123,
            #             'resourceRequirements': [
            #                 {
            #                     'value': 'string',
            #                     'type': 'GPU'|'InferenceAccelerator'
            #                 },
            #             ]
            #         },
            #     ],
            #     'cpu': 'string',
            #     'inferenceAcceleratorOverrides': [
            #         {
            #             'deviceName': 'string',
            #             'deviceType': 'string'
            #         },
            #     ],
            #     'executionRoleArn': 'string',
            #     'memory': 'string',
            #     'taskRoleArn': 'string'
            # },
            # placementConstraints=[
            #     {
            #         'type': 'distinctInstance'|'memberOf',
            #         'expression': 'string'
            #     },
            # ],
            # placementStrategy=[
            #     {
            #         'type': 'random'|'spread'|'binpack',
            #         'field': 'string'
            #     },
            # ],
            # platformVersion='string',
            propagateTags='TASK_DEFINITION', #'TASK_DEFINITION'|'SERVICE',
            referenceId=self.referenceId,
            startedBy=self.startedBy,
            # tags=[
            #     {
            #         'key': 'string',
            #         'value': 'string'
            #     },
            # ],
            taskDefinition=self.taskDefinition
        )

        self.log.debug(response)
        task_arns = [task['taskArn'] for task in response['tasks']]
        self.log.info(f"Creating tasks: {task_arns}")
        waiter = client.get_waiter('task_running')
        self.log.info("waiting for tasks to reach running state")
        waiter.wait(cluster=self.cluster, tasks=task_arns)
        self.log.info(f"tasks created: {task_arns}")
        if coordinator == True:
            self.log.info('Registering coordinator ip to airflow connections')
            host = self.get_task_private_IP(task_arns[0], cluster=self.cluster)
            self.register_connection(task_arns[0], 'presto', host, None, None, 8080)
            self.coordinator_host = host
            return host
        return None
