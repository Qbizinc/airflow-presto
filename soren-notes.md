1) Download astro docker image
   docker pull astronomerinc/ap-airflow:1.10.10-3-buster-onbuild

2) Run image with ports and mounts.
   docker run --rm -it -p 8080:8080 astronomerinc/ap-airflow:1.10.10-3-buster-onbuild bash

3) initalize the db.
   airflow initdb

4) login into container as root user and install presto
   docker exec -it -u root <container> bash
   pip3 install apache-airflow presto

5) Build and validate the qbiz-ecs-presto container.
   ```
   docker run --rm soren-presto-testing:latest
   ...
   2020-11-04T22:11:48.961Z        INFO    main    io.prestosql.server.Server      ======== SERVER STARTED ========
   ```
