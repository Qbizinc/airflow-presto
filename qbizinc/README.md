# Airflow ECS-Presto Operator

## Overview
This airflow operator manages the compute resources for you presto cluster,
as well as executing queries.  It manages all steps in a single airflow task.
Out of the box,  it works by:
- Starting the coordinator node.
- Capturing the public/private ip adress(es) of the the coordinator.
- Starting the worker nodes.
- Executing your query to the coordinator.
- Stopping all coordinator/workers.

## Prerequisites
- Docker image(s) for your coordinator and workers.
- ECS Cluster to manage the containers
- Task Definition(s) for ECS to orchestrate.
- Access to Hive Metadata (glue).
- Airflow, compute resource must allow the following IAM policies:
-- the ability create tasks on the ECS cluster, e.g. _AmazonECS_FullAccess_.
-- the ability to access the Elastic Container Registry, e.g. _AmazonEC2ContainerRegistryFullAccess_.
-- the ability to read/write data to S3, e.g. _AmazonS3FullAccess_.
-- the ability to access the AWS Glue service (Hive metadata store), e.g. _AWSGlueServiceRole_.

## Parameters overview

`task_id`  - Required for airflow dags -- task name.
`region_name` - aws region short name, e.g. _us-west-2_.
`cluster` - The name or ARN of you ECS cluster.
`count` - How many nodes you would like to launch.
`group` - A group name to easily identify all related nodes -- however you would
  like to logically group.  This tag is used to identify nodes started by the
  operator, when stopping the nodes.
`launchType` - 'EC2'|'FARGATE'  The example uses fargate.
`networkConfiguration` - a dictionary for network configuration:

- `awsvpcConfiguration`
    - `subnets` - 1 or more subnets
    - `securityGroups` - A security group that allows coordinator to be accessed from airflow
    - `assignPublicIp` - 'ENABLED'|'DISABLED' the example-dag uses enabled

`overrides` - a dictionary for docker container overrides

- `containerOverrides`
    - `name` - name of the image.  example dag uses 'Presto'
        - `environment` - for overriding environment variables
        - The example dag uses "MODE": "WORKER
            - `name` - env var name
            - `value` - env var value

`startedBy` - The way you want to identify "who" started this cluster.  This is used in order to identify which clusters should be removed.  So we add a uuid to the name to logically separate simultaneous/independent queries.
`taskDefinition` - The name or ARN of your task definition.
`query` - The query you'd like to send to presto.

## Operator execution
#### Customization
  By default,  the airflow task will run whatever is in the `execute` function of the operator.  You can customize how the airflow operator works by adjusting any of the steps in the `execute` function.

#### Debugging
  By default, if the operator does not successfully execute,  or get to the "spin down resources" phase, the operator will attempt to spin down aws resources and unregister the connection.  If this step fails, you will need to manually stop the running presto cluster tasks.  In your ECS cluster,  Identify the running tasks by group,  startedBy, or any other identifiable information,  and stop the tasks manually  