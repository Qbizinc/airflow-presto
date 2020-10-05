# Airflow ECS-Presto Operator

## Overview
This airflow operator manages the compute resources for you presto cluster,  as well as executing queries.  It manages all steps in a single airflow task.  Out of the box,  it works by:
- Starting the coordinator cluster
    - Capturing the public/private ip adress(es) of the the coordinator
    - registering the ip of the coordinator to airflow connections
- Starting the worker nodes
- Executing your query to the coordinator
- Stopping all coordinator/workers
- unregistering the airflow connection

## Prerequisites
- Docker image(s) for your coordinator and worker
- ECS Cluster to manage the containers
- Task Definition(s) for ECS to orchestrate
- Hive Metadata (glue)

## Parameters overview

`task_id`  - Required for airflow dags
`region_name` - aws configuration
`aws_access_key_id` - aws configuration
`aws_secret_access_key` - aws configuration
`cluster` - The name or ARN of you ecs cluster
`count` - How many worker nodes you would like to launch
`group` - A group name to easily identify all related nodes.  However you would like to logically group
`launchType` - 'EC2'|'FARGATE'  The example uses fargate
`networkConfiguration` - a dictionary for network configuration:

- `awsvpcConfiguration`
    - `subnets` - 1 or more subnets
    - `securityGroups` - A security group that allows coordinator to be accessed from airflow
    - `assignPublicIp` - 'ENABLED'|'DISABLED' the example-dag uses enabled

`overrides` - a dictionary for docker container overrides

- `containerOverrides` 
    - `name` - name of the image.  example dag uses 'Worker'
        - `environment` - for overriding environment variables
        - The example dag uses "MODE": "WORKER
            - `name` - env var name
            - `value` - env var value

`referenceId` - TODO: Not actually sure how this works, can maybe remove
`startedBy` - The way you want to identify "who" started this cluster.  This is used in order to identify which clusters should be removed.  So we add a uuid to the name to logically separate simultaneous/independent queries
`taskDefinition` - The name or ARN of your task definition
`query` - The query you'd like to send to presto

## Operator execution
#### Customization
  By default,  the airflow task will run whatever is in the `execute` function of the operator.  You can customize how the airflow operator works by adjusting any of the steps in the `execute` function.

#### Debugging
  By default, if the operator does not successfully execute,  or get to the "spin down resources" phase, the operator will attempt to spin down aws resources and unregister the connection.  If this step fails, you will need to manually stop the running presto cluster tasks.  In your ECS cluster,  Identify the running tasks by group,  startedBy, or any other identifiable information,  and stop the tasks manually  
