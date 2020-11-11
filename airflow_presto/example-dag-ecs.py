from airflow import DAG
from airflow.operators.dummy_operator import DummyOperator
from operators.presto_ecs_operator import ECSOperator

from datetime import datetime, timedelta
import json, uuid

ECSOperator.ui_color = "#00FFCC"

with open('/usr/local/airflow/dags/settings.json', 'r') as f:
    settings = json.load(f)

create_sql = """
CREATE TABLE IF NOT EXISTS default.test_tbl
(
    year VARCHAR,
    total double
) WITH (format='PARQUET')
"""

insert_sql = """
INSERT INTO default.test_tbl
SELECT year, SUM(total_amount) as total FROM default.ny_pub
GROUP BY year
"""

# Default settings applied to all tasks
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 0,
    'retry_delay': timedelta(minutes=5)
}

# Using a DAG context manager, you don't have to specify the dag property of each task
with DAG('ecs_dag',
         start_date=datetime(2020, 11, 6),
         max_active_runs=1,
         schedule_interval=timedelta(days=1),  # https://airflow.apache.org/docs/stable/scheduler.html#dag-runs
         default_args=default_args,
         catchup=True # enable if you don't want historical dag runs to run
         ) as dag:

    t0 = DummyOperator(
        task_id='start'
    )

    t1 = ECSOperator(
        params=settings,
        # This ID is how we know what to spin down when we are finished
        startedBy='airflow-' + str(uuid.uuid4()) ,
        query=insert_sql,
        task_id="ECS-Task-insert-table"
    )

    t0 >> t1
