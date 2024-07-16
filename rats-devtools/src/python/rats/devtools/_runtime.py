import json
import os
import uuid
from collections.abc import Callable
from typing import NamedTuple

import kubernetes

from rats import apps


class K8sRuntimeContext(NamedTuple):
    image: str
    command: tuple[str, ...]


class K8sRuntime(apps.Runtime):
    _ctx: apps.ConfigProvider[K8sRuntimeContext]
    _runtime: apps.Runtime

    def __init__(self, ctx: apps.ConfigProvider[K8sRuntimeContext], runtime: apps.Runtime) -> None:
        self._ctx = ctx
        self._runtime = runtime

    def execute(self, *exe_ids: apps.ServiceId[apps.T_ExecutableType]) -> None:
        """Execute a list of executables sequentially."""
        kubernetes.config.load_kube_config()
        new_id = self._make_ctx_id()
        remote_ctx = self._ctx()
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
                                        kubernetes.client.V1EnvVar("K8S_RUNTIME_CTX_ID", new_id),
                                        kubernetes.client.V1EnvVar(
                                            "K8S_RUNTIME_EXES", json.dumps(exe_ids)
                                        ),
                                    ],
                                    image_pull_policy="Always",
                                ),
                            ],
                            restart_policy="Never",
                        ),
                    ),
                ),
            )
            api_response = api_instance.create_namespaced_job(
                namespace=namespace,
                body=body,
            )
            print(f"job created: {api_response.metadata.name}")

    def execute_group(self, *exe_group_ids: apps.ServiceId[apps.T_ExecutableType]) -> None:
        """
        Execute one or more groups of executables sequentially.

        Although each group is expected to be executed sequentially, the groups themselves are not
        executed in a deterministic order. Runtime implementations are free to execute groups in
        parallel or in any order that is convenient.
        """
        kubernetes.config.load_kube_config()
        new_id = self._make_ctx_id()
        remote_ctx = self._ctx()
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
                                        kubernetes.client.V1EnvVar("K8S_RUNTIME_CTX_ID", new_id),
                                        kubernetes.client.V1EnvVar(
                                            "K8S_RUNTIME_GROUPS", json.dumps(exe_group_ids)
                                        ),
                                    ],
                                    image_pull_policy="Always",
                                ),
                            ],
                            restart_policy="Never",
                        ),
                    ),
                ),
            )
            api_response = api_instance.create_namespaced_job(
                namespace=namespace,
                body=body,
            )
            print(f"job created: {api_response.metadata.name}")

    def execute_callable(self, *callables: Callable[[], None]) -> None:
        raise RuntimeError("K8sRuntime does not support executing callables")

    def _make_ctx_id(self) -> str:
        return f"{self._ctx_id()}/{uuid.uuid4()!s}"

    def _ctx_id(self) -> str:
        return os.environ.get("K8S_RUNTIME_CTX_ID", "/")
