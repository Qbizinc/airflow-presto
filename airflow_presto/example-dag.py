import os
from airflow import DAG
from airflow.operators.dummy_operator import DummyOperator
from operators.presto_kubernetes_operator import PrestoKubernetesOperator
from datetime import datetime, timedelta


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
         start_date=datetime(2020, 8, 1),
         max_active_runs=3,
         schedule_interval=timedelta(days=1),  # https://airflow.apache.org/docs/stable/scheduler.html#dag-runs
         default_args=default_args,
         catchup=False  # enable if you don't want historical dag runs to run
         ) as dag:

    t0 = DummyOperator(
        task_id='start'
    )

    presto_kubernetes_op = PrestoKubernetesOperator(
        sql="SELECT '{{ds}}';",
        output_path='s3://etlresults/test_table/{{ds}}.csv',
        namespace='default',
        image="566283433843.dkr.ecr.us-east-1.amazonaws.com/presto-airflow:latest",
        labels={"project": "presto-airflow"},
        name="presto-output-test",
        task_id="presto-output-task",
        get_logs=True,
        dag=dag,
        config_file=os.environ['AIRFLOW_HOME'] + '/.kube/config',
        in_cluster=False,
        execution_timeout=timedelta(hours=1),
    )

    t1 = DummyOperator(
        task_id='end'
    )

    t0 >> presto_kubernetes_op >> t1
