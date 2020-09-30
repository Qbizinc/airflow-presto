from airflow import DAG
from airflow.operators.dummy_operator import DummyOperator
from airflow.operators.bash_operator import BashOperator
from airflow.operators.python_operator import PythonOperator
from operators.presto_ecs_operator import ECSOperator

from datetime import datetime, timedelta
from airflow.hooks.presto_hook import PrestoHook
import json, uuid

with open('credentials.json', 'r') as f:
    credentials = json.load(f)


# Default settings applied to all tasks
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5)
}

# Using a DAG context manager, you don't have to specify the dag property of each task
with DAG('example_dag',
         start_date=datetime(2020, 9, 25),
         max_active_runs=1,
         schedule_interval=timedelta(days=1),  # https://airflow.apache.org/docs/stable/scheduler.html#dag-runs
         default_args=default_args,
         catchup=False # enable if you don't want historical dag runs to run
         ) as dag:

    t0 = DummyOperator(
        task_id='start'
    )
    t1 = ECSOperator(
        region_name='us-west-2',
        aws_access_key_id=credentials['aws_access_key_id'],
        aws_secret_access_key=credentials['aws_secret_access_key'],
        task_id='run_presto_query',
        cluster='Soren-Presto-Cluster',
        count=2,
        group='airflow_ecs_operator',
        launchType='FARGATE', #'EC2'|'FARGATE'
        networkConfiguration={
            'awsvpcConfiguration': {
                'subnets': [
                    'subnet-d02fbc89',
                ],
                'securityGroups': [
                    'sg-07f31eb2e5e9b49ea',
                ],
                'assignPublicIp': 'ENABLED', #'ENABLED'|'DISABLED'
            }
        },
        overrides={
            'containerOverrides': [
                {
                    'name': 'Worker',
                    'environment': [
                        #{'name': 'COORDINATOR_HOST_PORT', 'value': '172.31.11.146'},
                        {'name': 'MODE','value': 'WORKER'},
                    ]
                }
            ]
        },
        referenceId=None,
        # This ID is how we know what to spin down when we are finished
        startedBy='airflow-' + str(uuid.uuid4()),
        taskDefinition='PrestoWorkers',
        query='select * from default.ny_pub LIMIT 10;'

    )
    t0 >> t1
