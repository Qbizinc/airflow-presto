import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

# 1) Jr. Candidate, coderpad interview.  Galvinize, commited through the end of the year.  Has done hackerRank and got 72 or 77 percent.  Ask when she was atually be able to start work.  Really not available until Jan?  If you accept will you commit to starting in Jan?  Are you ready to accept offer?  I need to
# schedule

# 2) Interesting opportunity to staff of 6 months, remotely, mostly West-cost hours, but sometimes in sweeden.  Possible to travel and work for there.  First ever opportunity from Mikhel.  Expertiese in Data Catalog Project, selection implimentation, etc...  Put together a list of questions about the project so we can get better idea of what they're looking for.  Ex.  Are you creating a data governece initiative?  Data quality initiative?  Data Linage?  Want to start the 21st of Jan.  $225/hr.  This afternoon, by EOD.

setuptools.setup(
    name="airflow_presto", # Replace with your own username
    version="0.0.1",
    author="Soren Archibald, Cameron Cole and Paco Valdez",
    author_email="soren@qbizinc.com",
    description="A containerized Presto cluster for AWS.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/QBizinc/airflow-presto",


    # Leave empty to package everything or pass a str representing a
    # directory to package -- to avoid packaging unit-tests, etc...
    # packages=setuptools.find_packages("airflow_presto"),
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
    install_requires=[
        'boto3 >= 1.7.84',
        'botocore >= 1.10.84',
        'apache-airflow >= 1.10.12',
        'PyHive >= 0.6.2']

    # must be collable.  This creates a simlink to
    # as class and executes a method?  See example at 10:56 of
    # https://www.youtube.com/watch?v=0W0k6zP_Lto
    # https://www.youtube.com/watch?v=-hENwoex93g
    # entry_points={
     #   'apache.plugins':
     #   ['airflow_presto = airflow_presto.operators.presto_ecs_operator:ECSOperator']
    #}
    # entry_points = {
     #   'airflow.plugins': [
     #       'my_plugin = airflow_presto.my_plugin:MyAirflowPlugin']
     #   }
)
