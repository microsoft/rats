import json
import subprocess
import uuid
from collections.abc import Callable, Mapping
from textwrap import dedent
from typing import NamedTuple
from urllib.parse import urlparse

import kubernetes

from rats import apps
from rats.devtools import ComponentOperations


class DevtoolsProcessContext(NamedTuple):
    cwd: str
    argv: tuple[str, ...]
    env: Mapping[str, str]


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
    _process_ctx: apps.ConfigProvider[DevtoolsProcessContext]
    _config: apps.ConfigProvider[K8sRuntimeContext]
    _devtools_ops: ComponentOperations
    _runtime: apps.Runtime

    def __init__(
        self,
        ctx_name: str,
        process_ctx: apps.ConfigProvider[DevtoolsProcessContext],
        config: apps.ConfigProvider[K8sRuntimeContext],
        devtools_ops: ComponentOperations,
        runtime: apps.Runtime,
    ) -> None:
        self._ctx_name = ctx_name
        self._process_ctx = process_ctx
        self._config = config
        self._devtools_ops = devtools_ops
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
        config = self._config()
        kubernetes.config.load_kube_config(context=self._ctx_name)
        new_id = self._make_ctx_id().strip("/")
        exes = json.dumps([exe._asdict() for exe in exe_ids])
        groups = json.dumps([group._asdict() for group in group_ids])

        self._devtools_ops.create_or_empty(self._devtools_ops.find_path(".tmp/k8s-job"))
        self._devtools_ops.copy_tree(
            self._devtools_ops.find_path("src/resources/base-k8s-job"),
            self._devtools_ops.find_path(".tmp/k8s-job"),
        )
        self._devtools_ops.find_path(".tmp/k8s-job/kustomization.yaml").write_text(
            dedent(
                f"""
            apiVersion: kustomize.config.k8s.io/v1beta1
            kind: Kustomization
            namespace: lolo
            resources:
            - namespace.yaml
            - job.yaml
            buildMetadata:
            - managedByLabel
            nameSuffix: '-{new_id[-4:]}'
            labels:
            - includeSelectors: true
              pairs:
                managedBy: rats-devtools
                workflow-id: '{new_id}'
            patches:
            - patch: |-
                apiVersion: batch/v1
                kind: Job
                metadata:
                  name: workflow
                spec:
                  template:
                    spec:
                      restartPolicy: Never
                      containers:
                        - name: main
                          image: {config.image}
                          command: ["echo", "hello, hello!"]
                          env:
                            - name: DEVTOOLS_K8S_CTX_ID
                              value: '{new_id}'
                            - name: DEVTOOLS_K8S_EXES
                              value: '{exes}'
                            - name: DEVTOOLS_K8S_GROUPS
                              value: '{groups}'
                          imagePullPolicy: Always
            """
            )
        )

        built = subprocess.run(
            ["kustomize", "build"],
            check=True,
            text=True,
            cwd=self._devtools_ops.find_path(".tmp/k8s-job"),
            capture_output=True,
        ).stdout
        subprocess.run(
            ["kubectl", "apply", "-f-"],
            check=True,
            text=True,
            cwd=self._devtools_ops.find_path(".tmp/k8s-job"),
            input=built,
        )
        print("job created: ... somewhere")

    def _make_ctx_id(self) -> str:
        return f"{self._ctx_id()}/{uuid.uuid4()!s}"

    def _ctx_id(self) -> str:
        return self._config().id
