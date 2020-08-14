# airflow_presto

## Airflow plugin

### Install
Copy directory `airflow_presto/operators/` to your plugins/ folder in your airflow deployment.
Your directory structure should look similar to this:

```
.
├── airflow.cfg
├── dags
│   └── example-dag.py
└── plugins
    └── operators
       └── presto_kubernetes_operator.py

```

There is an example of how to use the operator at:
`airflow_presto/example-dag.py`

## Presto
#### On-Demand Presto cluster deployment for Airflow.


Build image: 
```bash
docker build -f Dockerfile -t presto-airflow .
```

Specify Presto Version:

```bash
docker build -f Dockerfile -t presto-airflow --build-arg PRESTO_VERSION={version} .
```

Run Presto
```bash
docker run --env QUERY="Select 1;" presto-airflow
```



TO-DO:

* Add multi-node support to presto docker image
* Use `--file input.sql` from presto cli to pass an input file instead of the inline argument when a file is passed
* Package the module to make it pip-installable.
