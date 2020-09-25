from airflow import DAG
from airflow.operators.dummy_operator import DummyOperator
from airflow.operators.bash_operator import BashOperator
from airflow.operators.python_operator import PythonOperator
from airflow.operators.presto_ecs_operator import ECSOperator
from datetime import datetime, timedelta
from airflow.hooks.presto_hook import PrestoHook



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
         max_active_runs=3,
         schedule_interval=timedelta(minutes=30),  # https://airflow.apache.org/docs/stable/scheduler.html#dag-runs
         default_args=default_args,
         catchup=False # enable if you don't want historical dag runs to run
         ) as dag:

    t0 = DummyOperator(
        task_id='start'
    )
    t1 = ECSOperator(
        task_id='run_presto_query',
        cluster='Soren-Presto-Cluster',
        count=2,
        group='family:airflow_ecs_operator',
        launchType='FARGATE', #'EC2'|'FARGATE'
        networkConfiguration={
            'awsvpcConfiguration': {
                'subnets': [
                    'subnet-d02fbc89',
                ],
                # 'securityGroups': [
                #     'string',
                # ],
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
        startedBy='airflow',
        taskDefinition='PrestoWorkers',
        query='select * from system.runtime.nodes;'

    )

    '''
    t1 = DummyOperator(
        task_id='group_bash_tasks'
    )
    t2 = BashOperator(
        task_id='bash_print_date1',
        bash_command='sleep $[ ( $RANDOM % 30 )  + 1 ]s && date')
    t3 = BashOperator(
        task_id='bash_print_date2',
        bash_command='sleep $[ ( $RANDOM % 30 )  + 1 ]s && date')

    # generate tasks with a loop. task_id must be unique
    for task in range(5):
        tn = PythonOperator(
            task_id=f'python_print_date_{task}',
            python_callable=my_custom_function,  # make sure you don't include the () of the function
            op_kwargs={'task_number': task},
            provide_context=True
        )


        t0 >> tn # indented inside for loop so each task is added downstream of t0

    t0 >> t1
    t1 >> [t2, t3] # lists can be used to specify mutliple tasks
    '''
    t0 >> t1