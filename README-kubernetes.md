# airflow_presto

## Airflow plugin

### Setup custom Airflow Operator

Custom hooks and operators are a powerful way to extend Airflow to meet your needs. There is however some confusion on the best way to implement them. According to the Airflow documentation, they can be added using Airflow’s Plugins mechanism. This however, overcomplicates the issue and leads to confusion for many people. 
Airflow is even considering deprecating using the Plugins mechanism for hooks and operators going forward.

**Note**: The Plugins mechanism still must be used for plugins that make changes to the webserver UI.
How it works
You will need to have your Airflow Home directory with the following structure.
```
.
├── airflow.cfg
├── airflow.db
├── dags
│   └── example-dag.py
└── plugins
    └── operators
       └── presto_kubernetes_operator.py
```
When Airflow is running, it will add dags/, plugins/, and config/ to PATH, any python files in those folders should be accessible to import. 
So from our example-dag.py file, we can simply use
from operators.presto_kubernetes_operator import PrestoKubernetesOperator
And that's it! There is no need to define an AirflowPlugin class in any of the files, also no need for __init__ files in the operators and dags folders.
Note: If you use an IDE and don't want to get import errors, add the plugins directory as a source root.
Below is the code for each of the files so you can see how all the imports work. You can copy this files directly from the directory where you cloned the Qbiz repo: 
```
cp ~/airflow-presto/example-dag.py ~/<directory-name>/dags/example-dag.py

cp ~/airflow-presto/operators/presto_kubernetes_operator.py ~/<directory-name>/plugins/operators/presto_kubernetes_operator.py
```
You will need to replace <aws_account> with your AWS account in the file example-dag.py.


## Presto
#### On-Demand Presto cluster deployment for Airflow.

Create an ECR repository in your account named presto-airflow.

Then move to the docker directory:
cd docker

Retrieve an authentication token and authenticate your Docker client to your registry:

```aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <aws_account>.dkr.ecr.us-east-1.amazonaws.com```

Build the docker image:

```docker build -f Dockerfile -t presto-airflow .```

After the build completes, tag your image so you can push the image to this repository:

```docker tag presto-airflow:latest <aws_account>.dkr.ecr.us-east-1.amazonaws.com/presto-airflow:latest```

Run the following command to push this image to your newly created AWS repository:

```docker push <aws_account>.dkr.ecr.us-east-1.amazonaws.com/presto-airflow:latest```




TO-DO:

* Add multi-node support to presto docker image
