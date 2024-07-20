import json
import subprocess
import uuid
from collections.abc import Callable, Mapping
from hashlib import sha256
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
        # two very good seeds, if you want to reproduce a run
        new_id = self._make_ctx_id()
        run_id = sha256(new_id.encode()).hexdigest()
        workflow_stage = self._devtools_ops.find_path(f".tmp/workflow-runs/{run_id}")

        try:
            workflow_stage.mkdir(parents=True, exist_ok=False)
        except FileExistsError as e:
            raise RuntimeError(f"workflow run with id {run_id} already exists") from e

        exes = json.dumps([exe._asdict() for exe in exe_ids])
        groups = json.dumps([group._asdict() for group in group_ids])

        self._devtools_ops.copy_tree(
            self._devtools_ops.find_path("src/resources/k8s-components/workflow"),
            # our events should operate as if they run from the workflow staging directory
            workflow_stage / "workflow",
        )
        (workflow_stage / "patch-1.yaml").write_text(
            dedent(
                f"""
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
                          env:
                            - name: DEVTOOLS_K8S_CTX_ID
                              value: '{new_id}'
                            - name: DEVTOOLS_K8S_RUN_ID
                              value: '{run_id}'
                            - name: DEVTOOLS_K8S_EXES
                              value: '{exes}'
                            - name: DEVTOOLS_K8S_GROUPS
                              value: '{groups}'
                          imagePullPolicy: Always
                """
            )
        )
        (workflow_stage / "resource-1.yaml").write_text(
            dedent(
                f"""
                apiVersion: batch/v1
                kind: Job
                metadata:
                  name: workflow
                spec:
                  template:
                    spec:
                      restartPolicy: Never
                      containers:
                        - name: another
                          image: {config.image}
                """
            )
        )
        (workflow_stage / "kustomization.yaml").write_text(
            dedent(
                f"""
            apiVersion: kustomize.config.k8s.io/v1beta1
            kind: Kustomization
            nameSuffix: -{run_id[:5]}
            resources:
            - workflow
            patches:
            - path: resource-1.yaml
            - path: patch-1.yaml
            """
            )
        )

        built = subprocess.run(
            ["kustomize", "build"],
            check=True,
            text=True,
            cwd=workflow_stage,
            capture_output=True,
        ).stdout
        subprocess.run(
            ["kubectl", "apply", "-f-"],
            check=True,
            text=True,
            cwd=workflow_stage,
            input=built,
        )
        print("job created: ... somewhere")

    def _make_ctx_id(self) -> str:
        return f"{self._ctx_id()}/{uuid.uuid4()!s}"

    def _ctx_id(self) -> str:
        return self._config().id
