# airflow_presto

## Airflow plugin

### Install
Copy directory `airflow_presto/` to plugins/ folder in your airflow deployment.


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
