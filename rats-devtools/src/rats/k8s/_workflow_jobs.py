from collections.abc import Collection
from pathlib import Path

import yaml
from kubernetes import client
from kubernetes.client.rest import ApiException

from rats import app_context, apps, projects

from ._kustomize import KustomizeImage
from ._utils import hash_value, safe_value


class CreateNamespace(apps.Executable):
    _k8s_client: client.CoreV1Api
    _namespace_name: str

    def __init__(
        self,
        k8s_client: client.CoreV1Api,
        namespace_name: str,
    ) -> None:
        self._k8s_client = k8s_client
        self._namespace_name = namespace_name

    def execute(self) -> None:
        # Attempt to create the namespace directly
        namespace_manifest = client.V1Namespace(
            metadata=client.V1ObjectMeta(name=self._namespace_name)
        )

        try:
            self._k8s_client.create_namespace(body=namespace_manifest)
        except ApiException as e:
            if e.status == 409:
                # Namespace already exists (Conflict), which is fine
                pass
            else:
                # Re-raise other API exceptions
                raise


class KustomizeBuild(apps.Executable):
    _ctools: projects.ComponentTools
    _run_id: str
    _resource_path: Path
    _staging_path: Path
    _images: Collection[KustomizeImage]
    _main_component: str
    _app_ids: Collection[str]
    _ctx_collection: app_context.Collection

    def __init__(
        self,
        ctools: projects.ComponentTools,
        run_id: str,
        resource_path: Path,
        staging_path: Path,
        images: Collection[KustomizeImage],
        main_component: str,
        app_ids: Collection[str],
        ctx_collection: app_context.Collection,
    ) -> None:
        self._ctools = ctools
        self._run_id = run_id
        self._resource_path = resource_path
        self._staging_path = staging_path
        self._images = images
        self._main_component = main_component
        self._app_ids = app_ids
        self._ctx_collection = ctx_collection

    def execute(self) -> None:
        self._create_staging_workflow()
        self._create_kustomization()
        self._create_main_container_patch()

    def _create_staging_workflow(self) -> None:
        self._ctools.copy_tree(
            self._resource_path,
            self._staging_path / "workflow",
        )

    def _create_kustomization(self) -> None:
        (self._staging_path / "kustomization.yaml").write_text(
            yaml.safe_dump(
                {
                    "apiVersion": "kustomize.config.k8s.io/v1beta1",
                    "kind": "Kustomization",
                    "nameSuffix": f"-{safe_value(self._run_id)}",
                    "labels": [
                        {
                            "includeSelectors": True,
                            "pairs": {
                                # this one is human readable but not guaranteed unique
                                "rats.k8s/safe-run-id": safe_value(self._run_id),
                                # this one is most useful as a selector for uniqueness
                                "rats.k8s/run-id-hash": hash_value(self._run_id),
                            },
                        }
                    ],
                    "commonAnnotations": {
                        "rats.k8s/run-id": self._run_id,
                        "rats.k8s/safe-run-id": safe_value(self._run_id),
                        "rats.k8s/run-id-hash": hash_value(self._run_id),
                    },
                    "images": [image._asdict() for image in self._images],
                    "resources": ["workflow"],
                    "patches": [{"path": "main-container.yaml"}],
                },
                sort_keys=False,
            )
        )

    def _create_main_container_patch(self) -> None:
        (self._staging_path / "main-container.yaml").write_text(
            yaml.safe_dump(
                {
                    "apiVersion": "batch/v1",
                    "kind": "Job",
                    "metadata": {"name": "workflow"},
                    "spec": {
                        "template": {
                            "spec": {
                                "containers": [
                                    {
                                        "name": "main",
                                        "image": self._main_component,
                                        "command": ["rats-runtime", "run", *self._app_ids],
                                        "env": [
                                            {
                                                "name": "RATS_RUNTIME_RUN_CONTEXT",
                                                "value": app_context.dumps(self._ctx_collection),
                                            }
                                        ],
                                        "volumeMounts": [
                                            {
                                                "name": "podinfo",
                                                "mountPath": "/etc/podinfo",
                                            }
                                        ],
                                    }
                                ],
                                "volumes": [
                                    {
                                        "name": "podinfo",
                                        "downwardAPI": {
                                            "items": [
                                                {
                                                    "path": "annotations/rats.k8s/run-id",
                                                    "fieldRef": {
                                                        "fieldPath": "metadata.annotations['rats.k8s/run-id']",
                                                    },
                                                },
                                                {
                                                    "path": "annotations/rats.k8s/safe-run-id",
                                                    "fieldRef": {
                                                        "fieldPath": "metadata.annotations['rats.k8s/safe-run-id']",
                                                    },
                                                },
                                                {
                                                    "path": "annotations/rats.k8s/run-id-hash",
                                                    "fieldRef": {
                                                        "fieldPath": "metadata.annotations['rats.k8s/run-id-hash']",
                                                    },
                                                },
                                            ],
                                        },
                                    }
                                ],
                            },
                        },
                    },
                }
            ),
        )
