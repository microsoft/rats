# import datetime
# import logging
# import time
# import uuid
# from abc import abstractmethod
# from typing import Any, Dict, List, Optional, Protocol, Tuple, Union
#
# import kubernetes
# from kubernetes.client import V1Container, V1ResourceRequirements
#
# from oneml.pipelines.building._remote_execution import RemotePipelineSettings
# from oneml.pipelines.context._client import IProvideExecutionContexts
# from oneml.pipelines.dag import PipelineNode
# from oneml.pipelines.session import IExecutable
# from oneml.pipelines.session._session_client import PipelineSessionClient
# from oneml.pipelines.settings import IProvidePipelineSettings
# from ._logging import LogTailerThread
#
# logger = logging.getLogger(__name__)
#
#
# class IProvideK8sNodeCmds(Protocol):
#     @abstractmethod
#     def get_k8s_node_cmd(self, node: PipelineNode) -> Tuple[str, ...]:
#         pass
#
#
# class K8sJobSettings:
#     _session: PipelineSessionClient
#     _pipeline_settings: IProvidePipelineSettings
#     _cmd_client: IProvideK8sNodeCmds
#     _node: PipelineNode
#
#     def __init__(
#         self,
#         session: PipelineSessionClient,
#         pipeline_settings: IProvidePipelineSettings,
#         cmd_client: IProvideK8sNodeCmds,
#         node: PipelineNode,
#     ) -> None:
#         self._session = session
#         self._pipeline_settings = pipeline_settings
#         self._cmd_client = cmd_client
#         self._node = node
#
#     def get_job_name(self) -> str:
#         session_id = self._session_id()
#         node = self._node
#         execution_id = self._execution_id()
#         return f"oneml-{session_id[-4:]}-{node.name[-10:]}-{execution_id[-4:]}".lower()
#
#     def get_docker_image(self) -> str:
#         return self._pipeline_settings.get(RemotePipelineSettings.DOCKER_IMAGE)
#
#     def get_namespace(self) -> str:
#         return "development-workflows"
#
#     def get_cmd(self) -> Tuple[str, ...]:
#         return self._cmd_client.get_k8s_node_cmd(self._node)
#
#     def get_env(self) -> List[Dict[str, Union[str, Dict[Any, Any]]]]:
#         return [
#             {
#                 "name": "POD_CONTROLLER_UID",
#                 "valueFrom": {"fieldRef": {"fieldPath": "metadata.labels['controller-uid']"}},
#             },
#             {
#                 "name": "POD_CONTROLLER_NAME",
#                 "valueFrom": {"fieldRef": {"fieldPath": "metadata.labels['job-name']"}},
#             },
#             {
#                 # Just seems nice to always expose the IP to the running code
#                 "name": "HOST_IP",
#                 "valueFrom": {"fieldRef": {"fieldPath": "status.podIP"}},
#             },
#             {
#                 # And maybe the pod name too?
#                 "name": "POD_NAME",
#                 "valueFrom": {"fieldRef": {"fieldPath": "metadata.name"}},
#             },
#             {
#                 "name": "PIPELINE_SESSION_ID",
#                 "value": self._session_id(),
#             },
#         ]
#
#     def get_labels(self) -> Dict[str, str]:
#         return {
#             "execution-id": self._execution_id(),
#             "aadpodidbinding": "development-workflow",
#         }
#
#     def get_gb_memory(self) -> float:
#         return 4.0
#
#     def get_cpu_cores(self) -> float:
#         return 4.0
#
#     def get_gpu_count(self) -> int:
#         return 0
#
#     def _session_id(self) -> str:
#         return self._session.session_id()
#
#     def _execution_id(self) -> str:
#         return str(uuid.uuid4())
#
#
# class K8sExecutable(IExecutable):
#
#     _job_settings: K8sJobSettings
#
#     def __init__(
#         self,
#         job_settings: K8sJobSettings,
#     ) -> None:
#         self._job_settings = job_settings
#
#     def execute(self) -> None:
#         job_name = self._job_settings.get_job_name()
#         docker_image = self._job_settings.get_docker_image()
#         namespace = self._job_settings.get_namespace()
#         cmd = self._job_settings.get_cmd()
#         env = self._job_settings.get_env()
#         labels = self._job_settings.get_labels()
#         gb_memory = self._job_settings.get_gb_memory()
#         cpu_cores = self._job_settings.get_cpu_cores()
#         gpu_count = self._job_settings.get_gpu_count()
#
#         resource_requirements = V1ResourceRequirements(
#             limits={
#                 "memory": f"{gb_memory}Gi",
#                 "cpu": f"{cpu_cores}",
#                 "nvidia.com/gpu": f"{gpu_count}",
#             },
#         )
#
#         try:
#             kubernetes.config.load_kube_config()
#         except kubernetes.config.config_exception.ConfigException:
#             kubernetes.config.load_incluster_config()
#
#         logger.info(f"Creating Kubernetes Job: {job_name}")
#         logger.info(f"Job Labels: {labels}")
#
#         batch_v1 = kubernetes.client.BatchV1Api()
#         core_v1 = kubernetes.client.CoreV1Api()
#
#         # Configure Pod template container
#         containers = [
#             V1Container(
#                 name="job",
#                 image=docker_image,
#                 command=cmd,
#                 env=env,
#                 resources=resource_requirements,
#                 # TODO: remove when we can auto-build images again
#                 image_pull_policy="Always",
#             )
#         ]
#
#         # Create and configure a spec section
#         template = kubernetes.client.V1PodTemplateSpec(
#             metadata=kubernetes.client.V1ObjectMeta(labels=labels),
#             spec=kubernetes.client.V1PodSpec(
#                 service_account_name="development-workflow",
#                 restart_policy="Never",
#                 containers=containers,
#             ),
#         )
#
#         # Create the specification of deployment
#         spec = kubernetes.client.V1JobSpec(
#             template=template,
#             # No retries for now!
#             backoff_limit=0,
#         )
#
#         owner_references = None
#
#         # Instantiate the job object
#         job = kubernetes.client.V1Job(
#             api_version="batch/v1",
#             kind="Job",
#             metadata=kubernetes.client.V1ObjectMeta(
#                 name=job_name, owner_references=owner_references
#             ),
#             spec=spec,
#         )
#
#         batch_v1.create_namespaced_job(body=job, namespace=namespace)
#         logger.info("Workflow was scheduled in Kubernetes")
#
#         watcher: Optional[LogTailerThread] = None
#
#         while True:
#             response = batch_v1.read_namespaced_job(
#                 name=job_name,
#                 namespace=namespace,
#             )
#             is_done = response.status.succeeded is not None
#             is_running = response.status.active or 0
#             failures = response.status.failed or 0
#             start_time = response.status.start_time
#             if not start_time:
#                 logger.info("Job does not seem to have started yet")
#             else:
#                 now = datetime.datetime.now(datetime.timezone.utc)
#                 runtime = now - start_time
#                 if is_done:
#                     if watcher:
#                         watcher.terminate()
#
#                     if is_running or failures:
#                         # We seem to have a complete run but also stuff already running or failed
#                         # Something really odd happened
#                         raise RuntimeError(f"Impossible state detected: {response.status}")
#                     # Everything looks fine
#                     logger.info(
#                         f"Job completed <{job_name}>: {start_time} "
#                         f"to {now} - {runtime.total_seconds()}s"
#                     )
#                     return
#                 elif failures:
#                     raise RuntimeError("Job failure detected :( go check logs!")
#                 else:
#                     logger.info(
#                         f"Job not complete <{job_name}>: {start_time} "
#                         f"- {runtime.total_seconds()}s"
#                     )
#
#                 search = core_v1.list_namespaced_pod(
#                     namespace=namespace, label_selector=f"job-name={job_name}"
#                 )
#
#                 if len(search.items) == 1 and self._pod_is_ready(search.items[0]):
#                     if not watcher:
#                         watcher = LogTailerThread(search.items[0], core_v1)
#                         watcher.start()
#
#             time.sleep(5)
#
#     def _pod_is_ready(self, pod: Any) -> bool:
#         phase = pod.status.phase
#         logger.info(f"Pod state: {phase}")
#         if phase == "Pending":
#             return False
#         elif phase in ["Running", "Succeeded"]:
#             return True
#
#         raise RuntimeError(f"Pod in unknown state: {phase}")
#
#
# class K8sExecutableProxy(IExecutable):
#     """
#     This class is needed because we cannot get the active node before a app is created.
#     """
#
#     _session_provider: IProvideExecutionContexts[PipelineSessionClient]
#     _settings_provider: IProvidePipelineSettings
#     _cmd_client: IProvideK8sNodeCmds
#
#     def __init__(
#         self,
#         settings_provider: IProvidePipelineSettings,
#         cmd_client: IProvideK8sNodeCmds,
#     ) -> None:
#         self._settings_provider = settings_provider
#         self._cmd_client = cmd_client
#
#     def execute(self) -> None:
#         raise NotImplementedError()
#         session = self._session_provider.get_context()
#         exe_client = session.node_executables_client()
#         node = exe_client.get_active_node()
#         job_settings = K8sJobSettings(session, self._settings_provider, self._cmd_client, node)
#
#         K8sExecutable(job_settings).execute()
