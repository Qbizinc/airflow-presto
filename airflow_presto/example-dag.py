from airflow import DAG
from airflow.operators.dummy_operator import DummyOperator
from airflow.operators.bash_operator import BashOperator
from airflow.operators.python_operator import PythonOperator
from operators.presto_ecs_operator import ECSOperator

from datetime import datetime, timedelta
from airflow.hooks.presto_hook import PrestoHook
import json, uuid

with open('settings.json', 'r') as f:
    settings = json.load(f)


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
         start_date=datetime(2020, 10, 6),
         max_active_runs=1,
         schedule_interval=timedelta(days=1),  # https://airflow.apache.org/docs/stable/scheduler.html#dag-runs
         default_args=default_args,
         catchup=False # enable if you don't want historical dag runs to run
         ) as dag:

    t0 = DummyOperator(
        task_id='start'
    )
    t1 = ECSOperator(
        region_name=settings["region_name"],
        aws_access_key_id=settings["aws_access_key_id"],
        aws_secret_access_key=settings["aws_secret_access_key"],
        task_id=settings["task_id"],
        cluster=settings["cluster"],
        count=settings["count"],
        group=settings["group"],
        launchType=settings["launchType"],
        networkConfiguration=settings["networkConfiguration"],
        overrides=settings["overrides"],
        referenceId=settings["referenceId"],
        # This ID is how we know what to spin down when we are finished
        startedBy='airflow-' + str(uuid.uuid4() ,
        taskDefinition=settings["taskDefinition"],
        query='select * from default.ny_pub LIMIT 10;'
    )
    t0 >> t1
