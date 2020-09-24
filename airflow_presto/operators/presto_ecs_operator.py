from airflow.hooks.presto_hook import PrestoHook
from airflow.models import BaseOperator
from airflow.utils.decorators import apply_defaults
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
            referenceId: str,
            startedBy: str,
            taskDefinition: str,
            *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.cluster = cluster
        self.count = count
        self.group = group
        self.launchType = launchType
        self.referenceId = referenceId
        self.startedBy = startedBy
        self.taskDefinition = taskDefinition

    def create_single_node_task(self):
        raise NotImplementedError

    def register_connection(self, task):



    def stop_ecs_task(self):
        # TODO: first query the groups then take it all down
        raise NotImplementedError
        response = client.stop_task(
            cluster='string',
            task='string',
            reason='string'
        )
        return response


    def create_ecs_task(self):
        client = boto3.client('ecs')
        response = client.run_task(
            # capacityProviderStrategy=[
            #     {
            #         'capacityProvider': 'FARGATE',
            #         # 'weight': 123,
            #         # 'base': 123
            #     },
            # ],
            cluster='external-test',
            count=2,
            enableECSManagedTags=True, #True|False,
            group='external-task-group-name',
            launchType='FARGATE', #'EC2'|'FARGATE',
            networkConfiguration={
                'awsvpcConfiguration': {
                    'subnets': [
                        'subnet-d02fbc89',
                    ],
                    # 'securityGroups': [
                    #     'string',
                    # ],
                    # 'assignPublicIp': 'ENABLED'|'DISABLED'
                }
            },
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
            referenceId='external-task-td',
            startedBy='camerons-query',
            # tags=[
            #     {
            #         'key': 'string',
            #         'value': 'string'
            #     },
            # ],
            taskDefinition='PrestoWorkers'
        )

        self.log.debug(response)
        task_arns = [task['taskArn'] for task in response['tasks']]
        self.log.info(f"Creating tasks: {task_arns}")
        waiter = client.get_waiter('task_running')
        self.log.info("waiting for tasks to reach running state")
        waiter.wait(cluster=self.cluster, tasks=task_arns)
        self.log.info(f"tasks created: {task_arns}")
        return None
