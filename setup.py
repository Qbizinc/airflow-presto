import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="qbiz-airflow-presto", # Replace with your own username
    version="0.1rc1",
    author="Soren Archibald, Cameron Cole and Paco Valdez",
    author_email="soren@qbizinc.com",
    description="A containerized Presto cluster for AWS.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/QBizinc/airflow-presto",


    # Leave empty to package everything or pass a str representing a
    # directory to package -- to avoid packaging unit-tests, etc...
    # packages=setuptools.find_packages("airflow_presto"),
    # namespace_packages = ['qbizinc.airflow'],
    packages=setuptools.find_namespace_packages(include=["qbizinc.airflow"], exclude=("tests",)),
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
)
