from airflow.plugins_manager import AirflowPlugin
from airflow_presto.operators.presto_kubernetes_operator import PrestoKubernetesOperator


class PrestoKubernetesPlugin(AirflowPlugin):
    name = "PrestoKubernetesPlugin"
    operators = [PrestoKubernetesOperator]
    # Leave in for explicitness
    hooks = []
    executors = []
    macros = []
    admin_views = []
    flask_blueprints = []
    menu_links = []
