# airflow-presto
On-Demand Presto cluster deployment for Airflow.

```bash
docker build -f Dockerfile -t presto-airflow .
```

Specify Presto Version

```bash
docker build -f Dockerfile -t presto-airflow --build-arg PRESTO_VERSION={version} .
```

Run Presto

```bash
docker run -p 8080:8080 --name presto presto-airflow
```
