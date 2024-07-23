import json
import subprocess
import uuid
from collections.abc import Callable
from hashlib import sha256
from textwrap import dedent
from typing import NamedTuple

import kubernetes
import yaml

from rats import apps
from rats.projects._components import ComponentId, ComponentOperations


class KustomizeImage(NamedTuple):
    name: str
    newName: str
    newTag: str

    @property
    def full_name(self) -> str:
        return f"{self.newName}:{self.newTag}"


class K8sRuntimeConfig(NamedTuple):
    id: str
    container_images: tuple[KustomizeImage, ...]
    main_component: ComponentId


class K8sWorkflowRun(apps.Executable):
    _devops_component: ComponentOperations
    _main_component: ComponentOperations
    _main_component_id: ComponentId
    _k8s_config_context: str
    _container_images: tuple[KustomizeImage, ...]

    _id: str
    _exe_ids: tuple[apps.ServiceId[apps.T_ExecutableType], ...]
    _group_ids: tuple[apps.ServiceId[apps.T_ExecutableType], ...]

    def __init__(
        self,
        devops_component: ComponentOperations,
        main_component: ComponentOperations,
        main_component_id: ComponentId,
        k8s_config_context: str,
        container_images: tuple[KustomizeImage, ...],
        id: str,
        exe_ids: tuple[apps.ServiceId[apps.T_ExecutableType], ...],
        group_ids: tuple[apps.ServiceId[apps.T_ExecutableType], ...],
    ) -> None:
        self._devops_component = devops_component
        self._main_component = main_component
        self._main_component_id = main_component_id
        self._k8s_config_context = k8s_config_context
        self._container_images = container_images
        self._id = id
        self._exe_ids = exe_ids
        self._group_ids = group_ids

    def execute(self) -> None:
        kubernetes.config.load_kube_config(context=self._k8s_config_context)
        run_id = self._id
        run_hash = sha256(run_id.encode()).hexdigest()
        short_hash = run_hash[:10]
        workflow_stage = self._devops_component.find_path(f".tmp/workflow-runs/{run_hash}")
        try:
            workflow_stage.mkdir(parents=True, exist_ok=False)
        except FileExistsError as e:
            raise RuntimeError(f"workflow run with id {run_id} already exists") from e

        exes_json = json.dumps([exe._asdict() for exe in self._exe_ids])
        groups_json = json.dumps([group._asdict() for group in self._group_ids])

        self._devops_component.copy_tree(
            # we will include this resource at a minimum
            self._devops_component.find_path("src/resources/k8s-components/workflow"),
            # our events should operate as if they run from the workflow staging directory
            workflow_stage / "workflow",
        )
        (workflow_stage / "main-container.yaml").write_text(
            dedent(
                f"""
                apiVersion: batch/v1
                kind: Job
                metadata:
                  name: workflow
                spec:
                  template:
                    spec:
                      containers:
                        - name: main
                          image: {self._main_component_id.name}
                          volumeMounts:
                            - name: podinfo
                              mountPath: /etc/podinfo
                      volumes:
                        - name: podinfo
                          downwardAPI:
                            items:
                              - path: "annotations/rats.kuberuntime/run-id"
                                fieldRef:
                                  fieldPath: metadata.annotations['rats.kuberuntime/run-id']
                              - path: "annotations/rats.kuberuntime/run-hash"
                                fieldRef:
                                  fieldPath: metadata.annotations['rats.kuberuntime/run-hash']
                              - path: "annotations/rats.kuberuntime/exe-ids"
                                fieldRef:
                                  fieldPath: metadata.annotations['rats.kuberuntime/exe-ids']
                              - path: "annotations/rats.kuberuntime/group-ids"
                                fieldRef:
                                  fieldPath: metadata.annotations['rats.kuberuntime/group-ids']
                """
            )
        )

        (workflow_stage / "kustomization.yaml").write_text(
            yaml.dump(
                {
                    "apiVersion": "kustomize.config.k8s.io/v1beta1",
                    "kind": "Kustomization",
                    "nameSuffix": f"-{run_hash[:5]}",
                    "commonLabels": {"rats.kuberuntime/short-hash": short_hash},
                    "commonAnnotations": {
                        "rats.kuberuntime/run-id": run_id,
                        "rats.kuberuntime/short-hash": short_hash,
                        "rats.kuberuntime/run-hash": run_hash,
                        "rats.kuberuntime/exe-ids": exes_json,
                        "rats.kuberuntime/group-ids": groups_json,
                    },
                    "images": [image._asdict() for image in self._container_images],
                    "resources": ["workflow"],
                    "patches": [{"path": "main-container.yaml"}],
                },
                sort_keys=False,
            )
        )

        built = subprocess.run(
            ["kustomize", "build"],
            check=True,
            text=True,
            cwd=workflow_stage,
            capture_output=True,
        ).stdout
        print(built)
        subprocess.run(
            ["kubectl", "apply", "-f-"],
            check=True,
            text=True,
            cwd=workflow_stage,
            input=built,
        )
        print("job created: ... somewhere")
        print(f"kubectl describe pod -l rats.kuberuntime/short-hash={short_hash}")


class K8sRuntime(apps.Runtime):
    _config: apps.ConfigProvider[K8sRuntimeConfig]
    _factory: Callable[[...], apps.Executable]

    def __init__(
        self,
        config: apps.ConfigProvider[K8sRuntimeConfig],
        factory: Callable[[...], apps.Executable],
    ) -> None:
        self._config = config
        self._factory = factory

    def execute(self, *exe_ids: apps.ServiceId[apps.T_ExecutableType]) -> None:
        """Execute a list of executables sequentially."""
        self._factory(
            id=self._make_ctx_id(),
            exe_ids=exe_ids,
            group_ids=(),
        ).execute()

    def execute_group(self, *exe_group_ids: apps.ServiceId[apps.T_ExecutableType]) -> None:
        """
        Execute one or more groups of executables sequentially.

        Although each group is expected to be executed sequentially, the groups themselves are not
        executed in a deterministic order. Runtime implementations are free to execute groups in
        parallel or in any order that is convenient.
        """
        self._factory(
            id=self._make_ctx_id(),
            exe_ids=(),
            group_ids=exe_group_ids,
        ).execute()

    def execute_callable(self, *callables: Callable[[], None]) -> None:
        raise RuntimeError("K8sRuntime does not support executing callables")

    def _make_ctx_id(self) -> str:
        return f"{self._ctx_id()}/{uuid.uuid4()!s}"

    def _ctx_id(self) -> str:
        return self._config().id
