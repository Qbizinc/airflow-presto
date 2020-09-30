from airflow.hooks.presto_hook import PrestoHook
from airflow.models import BaseOperator
from airflow.utils.decorators import apply_defaults
from airflow.exceptions import AirflowException
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
            region_name: str,
            aws_access_key_id: str,
            aws_secret_access_key: str,
            cluster: str,
            count: int,
            group: str,
            launchType: str,
            networkConfiguration: dict,
            overrides: dict,
            referenceId: str,
            startedBy: str,
            taskDefinition: str,
            query: str,
            *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.region_name = region_name
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self.client = boto3.client(
            'ecs',
            region_name=self.region_name,
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key)
        self.cluster = cluster
        self.count = count
        self.group = group
        self.launchType = launchType
        self.networkConfiguration = networkConfiguration
        self.overrides = overrides
        self.referenceId = referenceId
        self.startedBy = startedBy
        self.taskDefinition = taskDefinition
        self.query = query

    # def create_single_node_task(self):
    #     raise NotImplementedError

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
        self.connection = conn
        self.conn_id = conn_id

    def unregister_connection(self, connection):
        self.log.info(f"removing connection: {connection}")
        session = settings.Session()
        session.delete(connection)
        session.commit()

    def query_presto(self, query, conn_id):
        self.log.info(f"Querying {conn_id}")
        ph = PrestoHook(presto_conn_id=conn_id)
        records = ph.get_records(query)
        self.log.info(f"Query complete,  {len(records)} records retrieved")
        return records

    def get_task_ip_address(self, task, cluster, public=False):
        self.log.info(
            f"Retrieving IP address for task {task} on cluster {cluster}. public is {public}"
        )
        describe_response = self.client.describe_tasks(cluster=cluster, tasks=[task])
        # Assuming only the one task,  this grabs the Private IP of the task
        for detail in describe_response['tasks'][0]['attachments'][0]['details']:
            if public == False and detail['name'] == 'privateIPv4Address':
                ip_address = detail['value']
                self.log.info(f"task {task} is at private address {ip_address}")
                return ip_address
            if public == True and detail['name'] == 'networkInterfaceId':
                ec2_client = boto3.client(
                    'ec2',
                    region_name=self.region_name,
                    aws_access_key_id=self.aws_access_key_id,
                    aws_secret_access_key=self.aws_secret_access_key
                )
                ec2_response = ec2_client.describe_network_interfaces(
                    NetworkInterfaceIds=[detail['value']]
                )
                ip_address = ec2_response['NetworkInterfaces'][0]['Association']['PublicIp']
                self.log.info(f"task {task} is at public address {ip_address}")
                return ip_address
        self.log.error(
            f"IP discovery did not execute correctly, client response: {describe_response}"
        )

    def stop_ecs_task(self, cluster, group):
        # TODO: first query the groups then take it all down
        self.log.info(f"Retrieving tasks associated with {self.startedBy} in {cluster}")
        tasks= self.client.list_tasks(cluster=cluster, startedBy=self.startedBy)['taskArns']
        self.log.info(f"Tasks marked for stopping: {tasks}")
        for task in tasks:
            self.log.info(f"Stopping task: {task}")
            response = self.client.stop_task(
                cluster=cluster,
                task=task,
                reason="Query Complete"
            )
        waiter = self.client.get_waiter('tasks_stopped')
        waiter.wait(cluster=self.cluster, tasks=tasks)
        self.log.info('Tasks succesfully spun down')
        return None

    def create_ecs_task(self, coordinator: bool, count, overrides):
        response = self.client.run_task(
            # capacityProviderStrategy=[
            #     {
            #         'capacityProvider': 'FARGATE',
            #         # 'weight': 123,
            #         # 'base': 123
            #     },
            # ],
            cluster=self.cluster,
            count=count,
            # enableECSManagedTags=True, #True|False,
            group=self.group,
            launchType=self.launchType, #'EC2'|'FARGATE',
            networkConfiguration=self.networkConfiguration,
            overrides=overrides,
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
            # propagateTags='TASK_DEFINITION', #'TASK_DEFINITION'|'SERVICE',
            # referenceId=self.referenceId,
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
        waiter = self.client.get_waiter('tasks_running')
        self.log.info("waiting for tasks to reach running state")
        waiter.wait(cluster=self.cluster, tasks=task_arns)
        self.log.info(f"tasks created: {task_arns}")
        if coordinator == True:
            self.log.info('Registering coordinator ip to airflow connections')
            self.coordinator_host = self.get_task_ip_address(
                task_arns[0],
                cluster=self.cluster,
                public=True
            )
            self.register_connection(
                task_arns[0],
                'presto',
                self.coordinator_host,
                None,
                None,
                8080
            )
            # Return the private IP, so the workers can connect to the private IP
            return self.get_task_ip_address(task_arns[0], cluster=self.cluster, public=False)
        return None

    def execute(self, context):
        # create the coordinator register it as the airflow connection
        # assign self.conn_id and capture cooridinator's private ip
        coordinator_overrides = {
            'containerOverrides': [
                {
                    'name': 'Worker',
                    'environment': [
                        {'name': 'COORDINATOR_HOST_PORT', 'value': 'localhost'},
                        {'name': 'MODE', 'value': 'COORDINATOR'}
                    ]
                }
            ]
        }
        host_private_ip = self.create_ecs_task(
            coordinator=True,
            count=1,
            overrides=coordinator_overrides
        )
        # create the workers
        # TODO: sloppy as hell
        self.overrides['containerOverrides'][0]['environment'].append(
            {'name': 'COORDINATOR_HOST_PORT', 'value': host_private_ip}
        )
        self.create_ecs_task(coordinator=False, count=self.count, overrides=self.overrides)
        # send that query
        results = self.query_presto(self.query, self.conn_id)
        # Stop all containers
        self.stop_ecs_task(cluster=self.cluster, group=self.group)
        self.unregister_connection(self.connection)
        print(results)
        return results
