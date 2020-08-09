from airflow.contrib.operators.kubernetes_pod_operator import KubernetesPodOperator
from airflow.utils.decorators import apply_defaults


class PrestoKubernetesOperator(KubernetesPodOperator):
    """
    Executes a Presto SQL query in a Kubernetes Pod

    :param sql: sql query string or path to sql file. (templated)
    :type sql: str
    :param output_path: if specified a path in s3 to upload the Query results in CSV. (templated)
    :type output_path: str
    :param output_cmd: if specified a cmd to be executed with the following pattern:
        ${OUTPUT_CMD} out.csv ${OUTPUT_PATH}.
    :type output_cmd: str
    :param image: Docker image you wish to launch. Use the one provided in this plugin.
    :type image: str
    :param name: name of the pod in which the task will run, will be used (plus a random
        suffix) to generate a pod id (DNS-1123 subdomain, containing only [a-z0-9.-]).
    :type name: str
    :param cmds: entrypoint of the container. (templated)
        The docker images's entrypoint is used if this is not provided.
    :type cmds: list[str]
    :param arguments: arguments of the entrypoint. (templated)
        The docker image's CMD is used if this is not provided.
    :type arguments: list[str]
    :param image_pull_policy: Specify a policy to cache or always pull an image.
    :type image_pull_policy: str
    :param image_pull_secrets: Any image pull secrets to be given to the pod.
                               If more than one secret is required, provide a
                               comma separated list: secret_a,secret_b
    :type image_pull_secrets: str
    :param ports: ports for launched pod.
    :type ports: list[airflow.kubernetes.pod.Port]
    :param volume_mounts: volumeMounts for launched pod.
    :type volume_mounts: list[airflow.kubernetes.volume_mount.VolumeMount]
    :param volumes: volumes for launched pod. Includes ConfigMaps and PersistentVolumes.
    :type volumes: list[airflow.kubernetes.volume.Volume]
    :param labels: labels to apply to the Pod.
    :type labels: dict
    :param startup_timeout_seconds: timeout in seconds to startup the pod.
    :type startup_timeout_seconds: int
    :param name: name of the pod in which the task will run, will be used to
        generate a pod id (DNS-1123 subdomain, containing only [a-z0-9.-]).
    :type name: str
    :param env_vars: Environment variables initialized in the container. (templated)
    :type env_vars: dict
    :param secrets: Kubernetes secrets to inject in the container.
        They can be exposed as environment vars or files in a volume.
    :type secrets: list[airflow.kubernetes.secret.Secret]
    :param in_cluster: run kubernetes client with in_cluster configuration.
    :type in_cluster: bool
    :param cluster_context: context that points to kubernetes cluster.
        Ignored when in_cluster is True. If None, current-context is used.
    :type cluster_context: str
    :param reattach_on_restart: if the scheduler dies while the pod is running, reattach and monitor
    :type reattach_on_restart: bool
    :param labels: labels to apply to the Pod.
    :type labels: dict
    :param startup_timeout_seconds: timeout in seconds to startup the pod.
    :type startup_timeout_seconds: int
    :param get_logs: get the stdout of the container as logs of the tasks.
    :type get_logs: bool
    :param annotations: non-identifying metadata you can attach to the Pod.
                        Can be a large range of data, and can include characters
                        that are not permitted by labels.
    :type annotations: dict
    :param resources: A dict containing resources requests and limits.
        Possible keys are request_memory, request_cpu, limit_memory, limit_cpu,
        and limit_gpu, which will be used to generate airflow.kubernetes.pod.Resources.
        See also kubernetes.io/docs/concepts/configuration/manage-compute-resources-container
    :type resources: dict
    :param affinity: A dict containing a group of affinity scheduling rules.
    :type affinity: dict
    :param node_selectors: A dict containing a group of scheduling rules.
    :type node_selectors: dict
    :param config_file: The path to the Kubernetes config file. (templated)
    :param config_file: The path to the Kubernetes config file. (templated)
        If not specified, default value is ``~/.kube/config``
    :type config_file: str
    :param do_xcom_push: If do_xcom_push is True, the content of the file
        /airflow/xcom/return.json in the container will also be pushed to an
        XCom when the container completes.
    :type do_xcom_push: bool
    :param is_delete_operator_pod: What to do when the pod reaches its final
        state, or the execution is interrupted.
        If False (default): do nothing, If True: delete the pod
    :type is_delete_operator_pod: bool
    :param hostnetwork: If True enable host networking on the pod.
    :type hostnetwork: bool
    :param tolerations: A list of kubernetes tolerations.
    :type tolerations: list tolerations
    :param configmaps: A list of configmap names objects that we
        want mount as env variables.
    :type configmaps: list[str]
    :param pod_runtime_info_envs: environment variables about
                                  pod runtime information (ip, namespace, nodeName, podName).
    :type pod_runtime_info_envs: list[airflow.kubernetes.pod_runtime_info_env.PodRuntimeInfoEnv]
    :param security_context: security options the pod should run with (PodSecurityContext).
    :type security_context: dict
    :param dnspolicy: dnspolicy for the pod.
    :type dnspolicy: str
    :param schedulername: Specify a schedulername for the pod
    :type schedulername: str
    :param full_pod_spec: The complete podSpec
    :type full_pod_spec: kubernetes.client.models.V1Pod
    :param init_containers: init container for the launched Pod
    :type init_containers: list[kubernetes.client.models.V1Container]
    :param log_events_on_failure: Log the pod's events if a failure occurs
    :type log_events_on_failure: bool
    :param do_xcom_push: If True, the content of the file
        /airflow/xcom/return.json in the container will also be pushed to an
        XCom when the container completes.
    :type do_xcom_push: bool
    :param pod_template_file: path to pod template file
    :type pod_template_file: str
    """
    template_fields = ('cmds', 'arguments', 'env_vars', 'config_file', 'pod_template_file', 'sql',
                       'output_path')
    template_ext = ('.sql', '.hql')  # Older versions of Airflow dont work with single element tuples
    ui_color = '#1e6fd9'

    @apply_defaults
    def __init__(self,
                 sql,
                 output_path=None,
                 output_cmd=None,
                 cmds=None,
                 arguments=None,
                 env_vars=None,
                 pod_template_file=None,
                 config_file=None,
                 *args,
                 **kwargs):
        super(PrestoKubernetesOperator, self).__init__(*args,
                                                       cmds=cmds,
                                                       arguments=arguments,
                                                       env_vars=env_vars,
                                                       pod_template_file=pod_template_file,
                                                       config_file=config_file,
                                                       **kwargs)
        self.sql = sql
        self.output_path = output_path
        self.output_cmd = output_cmd
        self.cmds = cmds or []
        self.arguments = arguments or []
        self.env_vars = env_vars or {}
        self.config_file = config_file
        self.pod_template_file = pod_template_file

    def execute(self, context):
        self.log.info('Executing: %s', self.sql)
        # The docker image provided with this plugin receives the query through ENV variable.
        self.env_vars['QUERY'] = self.sql
        if self.output_path:
            self.env_vars['OUTPUT_PATH'] = self.output_path
        if self.output_cmd:
            self.env_vars['OUTPUT_CMD'] = self.output_cmd
        super().execute(context)

