The QBiz, inc. Airflow-Presto package provides an _Airflow Operator_ which
is designed to run containerized Presto nodes using Amazon's _Elastic Container Service_.  It is designed to dynamically create and destroy
_Fargate_ compute resources to minimize cost.  This package does not include
the Docker Image nor will it attempt to create other AWS resources necessary
launch ECS tasks -- although examples are provided.  A Dockerfile to
build your own image can be found in the [Qbiz Code Repository](https://github.com/Qbizinc/airflow-presto/blob/master/docker/Dockerfile).
