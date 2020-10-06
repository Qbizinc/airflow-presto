# ECS-based clusters
## Introduction
This document walks through the process of setting up and ECS cluster
to run a containerized Presto cluster -- but it should work for
may other clustered applications.  The are many options to choose from
when creating your cluster: EC2 instances or Fargate; whether to spin-up
resource on-demand or whether to commit resources to running 24x7, etc...
Mostly likely, an organizations options will be limited to those that
System Administrators agree to allow (most large companies will not
authorize applications to create and destroy EC2 instances to control
costs and manage risk).  These instructions assume Administrators will
allow the creation and deletion of resource managed by [Fargate](https://aws.amazon.com/fargate/),
Amazon's managed compute service that doesn't incur a cost while idle.  

## Things that you will need.
These instructions require the following:
1. An [Elastic Container Repository](https://aws.amazon.com/ecr/)
   (ECR) where a Presto Docker image will be
   stored.  The image will be pulled into a container when a resource is
   instantiated.  
1. An [Elastic Container Service](https://aws.amazon.com/ecs/) (ECS) Cluster.
1. A [Task Definition](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task_definitions.html), which is the configuration for your containers and
   resources.  In it, you will specify where the Docker image is stored
   (ECR), Docker configurations -- environment variables, mounts, etc... --
   Fargate resources -- such as the cpu and memory of the virtual EC2 instance --
    and the AWS Service Role the container will use while running.
1. An [AWS Service](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_create_for-service.html) Role for ECS Tasks, which allows access to AWS Glue and S3.
1. An [AWS S3](https://aws.amazon.com/s3/) bucket with some data.
1. An [AWS Glue](https://aws.amazon.com/glue/features/) database, with one or more tables defined for the data stored on
   S3.  You may need to define a Crawler to expose the data on S3 to Glue.

## Things to consider before you being
1. What region to use.
2. What VPC and subnets to use.

I provide example CLI commands, which use the following environment variables:
```bash
export BASE_NAME=soren
export AWS_PROFILE=qbiz
export AWS_DEFAULT_REGION=us-west-2
export CLUSTER_NAME=${BASE_NAME}-Presto-Cluster
export SERVICE_NAME=${BASE_NAME}ServiceRoleECS
export REPOSITORY_NAME=${BASE_NAME}-presto-testing
```

In addition, you will need to chose where you want your resources placed.
Set these values.  A _Public_ VPC is assumed.
```bash
export VPC_ID=vpc-********
export SUBNET=subnet-********
export SECURITY_GROUP=sg-******
````

## ECS Cluster
To create the ECR, use the AWS Console wizard or use the CLI, as followed:
```bash
aws ecs create-cluster $CLUSTER_NAME \
  --cluster-name  \
  --tags key=Owner,value=$BASE_NAME key=Project,value=Presto
```
This creates a an empty cluster, with no compute resources
allocated to it.

## ECR
Create a repository for the Docker image.  The Repositoy's ARM will be need to be referenced later.

```bash
REPO_RESULT=$(aws ecr create-repository \
  --repository-name $REPOSITORY_NAME)

echo $REPO_RESULT
export REPO_ARN=$(jq '.repository.repositoryArn' <<< "$REPO_RESULT" )
echo $REPO_ARN
```

## Build, tag and upload the image to ECR
Instruction on building a Docker image and uploading to ECR can be found on the Docker and Amazon websites.  I show the commands for my account below.  Your commands may vary based on account, region and ECR name.  Go to the ECR console for
your repository and follow the instructions under _View Push commands_.

## Task Execution Role
This role is for the resource that pulls and executes the
container.  
```bash
echo "Create IAM task exec role."
TASK_EXEC_OBJ=$(aws iam create-role \
  --role-name $TASK_EXECUTION_NAME \
  --description "Service role for an ECS task." \
  --assume-role-policy-document file://$PWD/document.json)

echo "Adding policy to IAM task exec role."
aws iam attach-role-policy \
  --role-name $(jq -r ".Role.RoleName" <<< $TASK_EXEC_OBJ) \
  --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy

```
## Task Role
Since our tasks (running Presto) will need to connect to a Hive metadata catalog,
we need to create an execution role for the container with access to the catalog
under Glue and access data on S3 (via Glue)

```bash
aws iam create-role \
  --role-name $SERVICE_NAME \
  --description "Service role for an ECS task." \
  --assume-role-policy-document file://$PWD/document.json

aws iam attach-role-policy \
  --role-name $SERVICE_NAME \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole

aws iam attach-role-policy \
  --role-name $SERVICE_NAME \
  --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess
```

## Task Defintion
Create a [_Task Definition_](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task_definitions.html) through the AWS Console or from the command-line.  The parameters for creating a Task Definition are lengthy, but possible.  However, I've chosen to create a definition in a file with JSON syntax, named task-definition.json, under the _ecs_ path in this repository.
```bash
aws ecs register-task-definition \
  --family $TASK_DEFINITION_NAME \
  --task-role-arn $SERVICE_NAME \
  --execution-role-arn $TASK_EXECUTION_NAME \
  --cli-input-json file://$PWD/task-definition.json > /dev/null
```

## Launch a Coordinator task
The coordinator is special in that it is the task to which the client connects,
delegates tasks to the workers and runs the discovery service.  All workers register
with the discovery service so the coordinator knows how many workers are available.
For this reason, the IP address of the coordinator must be known before the workers
can start.

Since this is the action that actually creates a physical compute resource,
it requires some physical attributes, such as the _subnets_ in which to launch
the compute and _security_group_ to use.  (Resources such as memory and cpu age
defined in the _task_definition_.)

```bash
aws ecs run-task \
  --cluster $CLUSTER_NAME \
  --count 1 \
  --reference-id coordinator \
  --task-definition $TASK_DEFINITION_NAME \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[$SUBNET],securityGroups=[$SECURITY_GROUP],assignPublicIp=ENABLED}"
```

## Launch a set of Worker tasks

The above task will return the IP address of the coordinator, this address plus
the port are necessary for the _COORDINATOR_HOST_PORT_ environment variable, e.g.
_192.168.1.230:8080_.  Note also, the _MODE_ environment variable needs to be
set to _WORKER_.  Workers will call the discovery URI and register with the
the coordinator.

Since workers are physical compute resources, they also require a subnet and security group.
```bash
aws ecs run-task \
  --cluster "$MYNAME-Presto-Cluster" \
  --count 1 \
  --reference-id worker \
  --task-definition soren-presto-testing \
  --launch-type FARGATE \
  --overrides [{"name":"Presto","environment":[{"name":"MODE","value":"WORKER"},{"name":"COORDINATOR_HOST_PORT","value":""}]}]
  --network-configuration "awsvpcConfiguration={subnets=[$SUBNET],securityGroups=[$SECURITY_GROUP],assignPublicIp=ENABLED}"
```
