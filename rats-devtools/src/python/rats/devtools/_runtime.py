import json
import uuid
from collections.abc import Callable
from typing import NamedTuple
from urllib.parse import urlparse

import kubernetes
from kubernetes.client import V1Job, V1ObjectMeta

from rats import apps


class K8sRuntimeContext(NamedTuple):
    id: str
    image_name: str
    image_tag: str
    command: tuple[str, ...]

    @property
    def image(self) -> str:
        return f"{self.image_name}:{self.image_tag}"

    @property
    def is_acr(self) -> bool:
        parts = str(urlparse(f"//{self.image_name}").hostname).split(".")
        return ".".join(parts[1:]) == "azurecr.io"


class K8sRuntime(apps.Runtime):
    _ctx_name: str
    _config: apps.ConfigProvider[K8sRuntimeContext]
    _runtime: apps.Runtime

    def __init__(
        self, ctx_name: str, config: apps.ConfigProvider[K8sRuntimeContext], runtime: apps.Runtime
    ) -> None:
        self._ctx_name = ctx_name
        self._config = config
        self._runtime = runtime

    def execute(self, *exe_ids: apps.ServiceId[apps.T_ExecutableType]) -> None:
        """Execute a list of executables sequentially."""
        self._exe_remote(exe_ids, ())

    def execute_group(self, *exe_group_ids: apps.ServiceId[apps.T_ExecutableType]) -> None:
        """
        Execute one or more groups of executables sequentially.

        Although each group is expected to be executed sequentially, the groups themselves are not
        executed in a deterministic order. Runtime implementations are free to execute groups in
        parallel or in any order that is convenient.
        """
        self._exe_remote((), exe_group_ids)

    def execute_callable(self, *callables: Callable[[], None]) -> None:
        raise RuntimeError("K8sRuntime does not support executing callables")

    def _exe_remote(
        self,
        exe_ids: tuple[apps.ServiceId[apps.T_ExecutableType], ...],
        group_ids: tuple[apps.ServiceId[apps.T_ExecutableType], ...],
    ) -> None:
        remote_ctx = self._config()
        kubernetes.config.load_kube_config(context=self._ctx_name)
        new_id = self._make_ctx_id()
        exes = json.dumps([exe._asdict() for exe in exe_ids])
        groups = json.dumps([group._asdict() for group in group_ids])
        with kubernetes.client.ApiClient() as api_client:
            # Create an instance of the API class
            api_instance = kubernetes.client.BatchV1Api(api_client)
            namespace = "default"
            body = kubernetes.client.V1Job(
                metadata=kubernetes.client.V1ObjectMeta(
                    name=f"rats-devtools-{new_id[2:5]}",
                ),
                spec=kubernetes.client.V1JobSpec(
                    template=kubernetes.client.V1PodTemplateSpec(
                        spec=kubernetes.client.V1PodSpec(
                            containers=[
                                kubernetes.client.V1Container(
                                    name="worker",
                                    image=remote_ctx.image,
                                    command=remote_ctx.command,
                                    env=[
                                        kubernetes.client.V1EnvVar("DEVTOOLS_K8S_CTX_ID", new_id),
                                        kubernetes.client.V1EnvVar("DEVTOOLS_K8S_EXES", exes),
                                        kubernetes.client.V1EnvVar("DEVTOOLS_K8S_GROUPS", groups),
                                    ],
                                    image_pull_policy="Always",
                                ),
                            ],
                            restart_policy="Never",
                        ),
                    ),
                ),
            )
            api_response: V1Job = api_instance.create_namespaced_job(  # type: ignore
                namespace=namespace,
                body=body,
            )
            meta: V1ObjectMeta = api_response.metadata  # type: ignore
            print(f"job created: {meta.name}")

    def _make_ctx_id(self) -> str:
        return f"{self._ctx_id()}/{uuid.uuid4()!s}"

    def _ctx_id(self) -> str:
        return self._config().id
