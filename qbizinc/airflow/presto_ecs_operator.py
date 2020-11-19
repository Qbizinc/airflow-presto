from airflow.plugins_manager import AirflowPlugin
from airflow.models import BaseOperator
from airflow.utils.decorators import apply_defaults
from airflow.exceptions import AirflowException
from airflow import settings
from airflow.models import Connection
import boto3
from botocore.config import Config
from pyhive import presto


class ECSOperator(BaseOperator):
    @apply_defaults
    def __init__(
            self,
            params: dict,
            startedBy: str,
            query: str,
            shutdown: bool = True,
            *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.params = params

        boto_client_config = Config(region_name=self.params['region_name'])
        self.client = boto3.client( 'ecs', config=boto_client_config )

        self.startedBy = startedBy
        self.shutdown = shutdown
        self.query = query

    def query_presto(self, query):
        presto_cursor = presto.connect(self.coordinator_host).cursor()
        presto_cursor.execute(query)
        records = presto_cursor.fetchall()
        self.log.info(f"Query complete,  {len(records)} records retrieved")
        return records

    def get_task_ip_address(self, task, public=False):
        self.log.info(
            f"Retrieving IP address for task {task} on cluster {self.params['cluster']}. public is {public}"
        )
        describe_response = self.client.describe_tasks(cluster=self.params["cluster"], tasks=[task])

        # Assuming only the one task,  this grabs the Private IP of the task
        for detail in describe_response['tasks'][0]['attachments'][0]['details']:
            if public == False and detail['name'] == 'privateIPv4Address':
                ip_address = detail['value']
                self.log.info(f"task {task} is at private address {ip_address}")
                return ip_address

            # Ask Cameron why this is here.
            if public == True and detail['name'] == 'networkInterfaceId':
                ec2_client = boto3.client(
                    'ec2',
                    region_name=self.params["region_name"]
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

    def stop_ecs_task(self):
        # TODO: first query the groups then take it all down
        self.log.info(f"Retrieving tasks associated with {self.startedBy} in {self.params['cluster']}")
        tasks = self.client.list_tasks(cluster=self.params["cluster"], startedBy=self.startedBy)['taskArns']
        self.log.info(f"Tasks marked for stopping: {tasks}")
        try:
            for task in tasks:
                self.log.info(f"Stopping task: {task}")
                response = self.client.stop_task(
                    cluster=self.params["cluster"],
                    task=task,
                    reason="Query Complete"
                )
            waiter = self.client.get_waiter('tasks_stopped')
            waiter.wait(cluster=self.params["cluster"], tasks=tasks)
        except Exception as e:
            self.log.critical('*** ECSOperator failed to spin down resources ***')
            raise(e)

        self.log.info('Tasks succesfully spun down')
        return None

    def create_ecs_task(self, coordinator: bool, count, overrides):
        response = self.client.run_task(
            cluster=self.params["cluster"],
            count=count,
            group=self.params["group"],
            launchType=self.params["launchType"], #'EC2'|'FARGATE',
            networkConfiguration=self.params["networkConfiguration"],
            overrides=overrides,
            startedBy=self.startedBy,
            taskDefinition=self.params["taskDefinition"]
        )

        self.log.debug(response)
        task_arns = [task['taskArn'] for task in response['tasks']]
        self.log.info(f"Creating tasks: {task_arns}")
        waiter = self.client.get_waiter('tasks_running')
        self.log.info("waiting for tasks to reach running state")
        waiter.wait(cluster=self.params["cluster"], tasks=task_arns)
        self.log.info(f"tasks created: {task_arns}")
        if coordinator == True:
            self.log.info('Registering coordinator ip to airflow connections')
            self.coordinator_host = self.get_task_ip_address(
                task_arns[0],
                public=True
            )
            # Return the private IP, so the workers can connect to the private IP
            self.log.info(f"Saving Coordinator IP address at: {self.coordinator_host}")
            return self.get_task_ip_address(task_arns[0],  public=False)
        return None

    def execute(self, context):
        """
        execute(self, context):

        This function is executed by Airflow and passes the DAG context -- if
        configured to do so.  The QBiz operator does not rely on the Airflow Context.

        This code creates a Coordinator and saves its IP address.  If worker nodes
        are requested, they are given the IP address of the coordinator and register
        themselves to the cluster.  Once all the cluster nodes are active, this
        function will send the query to the coordinator. Lastly, the ECS nodes
        are stopped.

        Of note: there will need to be connectivity between the Airflow workers
        (or scheduler) and the coordinator.  The best way to insure connectivity,
        is to have all applications running in the same network subnet.
        """
        try:
            # Environment Variables for the Coordinator.  QBiz has made just
            # one image for both coordinator and workers; these environment
            # variables control whether a container runs as a coordinator or
            # a worker.
            coordinator_overrides = {
                'containerOverrides': [
                    {
                        'name': 'Presto',
                        'environment': [
                            {'name': 'COORDINATOR_HOST_PORT', 'value': 'localhost'},
                            {'name': 'MODE', 'value': 'COORDINATOR'}
                        ]
                    }
                ]
            }

            # Create the Coordinator.
            host_private_ip = self.create_ecs_task(
                coordinator=True,
                count=1,
                overrides=coordinator_overrides
            )

            # The coordinator, as configured in the QBiz image, will
            # participate in performing the query.  Therefore, decrement
            # the number of nodes requested.
            worker_cnt = self.params["count"] - 1

            # create the workers, if necessary.
            if worker_cnt > 0:
                self.params["overrides"]['containerOverrides'][0]['environment'].append(
                    {'name': 'COORDINATOR_HOST_PORT', 'value': host_private_ip}
                )
                self.create_ecs_task(coordinator=False, count=worker_cnt, overrides=self.params["overrides"])

            # send that query
            results = self.query_presto(self.query)
            self.log.info(results)

            # Stop all containers and remove airflow connection
            if self.shutdown:
                self.stop_ecs_task()

            return results

        except Exception as e:
            # Something bad happened.  Attempt to spin down any created resources
            try:
                self.log.error(e)
                self.log.warning('ECSOperator failed execution')
                self.log.warning(f"Attempting to stop resources started by {self.startedBy}")
                self.stop_ecs_task()
                raise e

            except Exception as e2:
                # Spinning down resources failed.  Resources are still standing
                # Scream at the user about it
                self.log.critical('*** ECSOperator failed to spin down resources ***')
                self.log.critical(f"Check ECS cluster {self.params['cluster']} for idle tasks")
                self.log.critical(f"Tasks started by {self.startedBy}")
                raise e2

class MyAirflowPlugin(AirflowPlugin):
    name = 'qbizinc'
    operators = [ECSOperator]
