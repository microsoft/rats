import json
import logging
import os
import subprocess
import sys
from collections.abc import Iterator
from datetime import datetime
from functools import cache
from pathlib import Path
from typing import Any, NamedTuple
from uuid import uuid4

import click
import yaml
from kubernetes import client, config

from rats import app_context, apps, cli, logs, projects

from ._workflow_jobs import CreateNamespace

logger = logging.getLogger(__name__)


class KustomizeImage(NamedTuple):
    name: str
    newName: str
    newTag: str

    @property
    def full_name(self) -> str:
        return f"{self.newName}:{self.newTag}"


@apps.autoscope
class AppConfigs:
    K8S_CONFIG_CONTEXT = apps.ServiceId[str]("k8s-config-context")
    APP_CONTEXT = apps.ServiceId[app_context.Context[Any]]("app-context.config-group")
    """Service group containing context services to attach to the submitted k8s process."""
    RUN_ID = apps.ServiceId[str]("run-id")
    KUSTOMIZE_IMAGES = apps.ServiceId[KustomizeImage]("kustomize-images")


@apps.autoscope
class AppServices:
    RUN_STAGING_PATH = apps.ServiceId[Path]("run-staging-path")


class Application(apps.AppContainer, cli.Container, apps.PluginMixin):
    def execute(self) -> None:
        argv = self._app.get(cli.PluginConfigs.ARGV)
        cli.create_group(click.Group("rats-k8s"), self).main(
            args=argv[1:],
            prog_name=Path(argv[0]).name,
            auto_envvar_prefix="RATS_AML",
            # don't end the process
            standalone_mode=False,
        )

    @cli.command()
    @click.argument("app-ids", nargs=-1)
    @click.option("--context", default='{"items": []}')
    @click.option("--context-file")
    @click.option("--wait", is_flag=True, default=False, help="wait for completion of aml job.")
    def _test(
        self,
        app_ids: tuple[str, ...],
        context: str,
        context_file: str | None,
        wait: bool,
    ) -> None:
        # Get the Kubernetes context from the app configuration
        k8s_ctx_name = self._app.get(AppConfigs.K8S_CONFIG_CONTEXT)

        # Load the Kubernetes configuration with the specified context
        config.load_kube_config(context=k8s_ctx_name)

        # Create the Kubernetes client
        k8s_client = client.CoreV1Api()

        # Create and execute the CreateNamespace instance
        cn = CreateNamespace(k8s_client=k8s_client, namespace_name="workflows")
        cn.execute()

    @cli.command()
    @click.argument("app-ids", nargs=-1)
    @click.option("--context", default='{"items": []}')
    @click.option("--context-file")
    @click.option("--wait", is_flag=True, default=False, help="wait for completion of aml job.")
    def _submit(
        self,
        app_ids: tuple[str, ...],
        context: str,
        context_file: str | None,
        wait: bool,
    ) -> None:
        """
        Submit one or more apps to k8s.

        Run `rats-k8s list` to find the list of applications registered in this component.
        """
        self._app.get(AppConfigs.K8S_CONFIG_CONTEXT)
        # kubernetes.config.load_kube_config(context=k8s_ctx_name)

        ctx_collection = app_context.loads(context).add(
            *self._app.get_group(AppConfigs.APP_CONTEXT),
        )
        if context_file:
            p = Path(context_file)
            if not p.is_file():
                raise RuntimeError(f"context file not found: {context_file}")

            data = yaml.safe_load(p.read_text())
            ctx_collection = ctx_collection.merge(app_context.loads(json.dumps(data)))

        if len(app_ids) == 0:
            logging.warning("No applications were provided to the command")

        for a in app_ids:
            # make sure all these app ids are valid
            if a not in self._runtime_list():
                raise RuntimeError(f"app id not found: {a}")

        staging_path = self._app.get(AppServices.RUN_STAGING_PATH)
        staging_path.mkdir(parents=True, exist_ok=False)

        ctools = self._app.get(projects.PluginServices.CWD_COMPONENT_TOOLS)
        ctools.copy_tree(
            Path("src/rats_resources/k8s/workflow-jobs"),
            staging_path / "workflow",
        )

        self._create_kustomization()
        self._create_main_container_patch()

        built = subprocess.run(
            ["kubectl", "kustomize"],
            check=True,
            text=True,
            cwd=staging_path,
            capture_output=True,
        ).stdout
        logger.info(f"completed kustomize build\n{built}")

    def _create_kustomization(self) -> None:
        staging_path = self._app.get(AppServices.RUN_STAGING_PATH)
        run_id = self._app.get(AppConfigs.RUN_ID)
        kustomize_images = list(self._app.get_group(AppConfigs.KUSTOMIZE_IMAGES))
        (staging_path / "kustomization.yaml").write_text(
            yaml.safe_dump(
                {
                    "apiVersion": "kustomize.config.k8s.io/v1beta1",
                    "kind": "Kustomization",
                    "nameSuffix": f"-{run_id}",
                    "labels": [
                        {
                            "includeSelectors": True,
                            "pairs": {
                                "rats.k8s/run-id": run_id,
                            },
                        }
                    ],
                    "commonAnnotations": {
                        "rats.k8s/run-id": run_id,
                    },
                    "images": [image._asdict() for image in kustomize_images],
                    "resources": ["workflow"],
                    "patches": [{"path": "main-container.yaml"}],
                },
                sort_keys=False,
            )
        )

    def _create_main_container_patch(self) -> None:
        staging_path = self._app.get(AppServices.RUN_STAGING_PATH)
        (staging_path / "main-container.yaml").write_text(
            yaml.safe_dump(
                {
                    "apiVersion": "batch/v1",
                    "kind": "Job",
                    "metadata": {"name": "workflow"},
                    "spec": {
                        "template": {
                            "spec": {
                                "containers": self._containers(),
                                "volumes": self._volumes(),
                            },
                        },
                    },
                }
            ),
        )

    def _containers(self) -> list[dict[str, Any]]:
        return [
            {
                "name": "main",
                "image": "rats-devtools",
                "command": ["echo", "hello, world!"],
                "env": [],
                "volumeMounts": [
                    {
                        "name": "podinfo",
                        "mountPath": "/etc/podinfo",
                    }
                ],
            }
        ]

    def _volumes(self) -> list[dict[str, Any]]:
        return [
            {
                "name": "podinfo",
                "downwardAPI": {
                    "items": [
                        {
                            "path": "annotations/rats.kuberuntime/run-id",
                            "fieldRef": {
                                "fieldPath": "metadata.annotations['rats.kuberuntime/run-id']",
                            },
                        },
                    ],
                },
            }
        ]

    @cache  # noqa: B019
    def _runtime_list(self) -> tuple[str, ...]:
        """
        Uses the `rats-runtime list` command within the component `rats-k8s list` is run from.

        Making this a simple subprocess allows us to submit to k8s from components that have
        no k8s libraries installed, even when the `rats-devtools` component is not installed.
        """
        response = subprocess.run(["rats-runtime", "list"], capture_output=True)
        return tuple(response.stdout.decode("UTF-8").splitlines())

    @apps.service(AppServices.RUN_STAGING_PATH)
    def _run_staging_path(self) -> Path:
        ctools = self._app.get(projects.PluginServices.CWD_COMPONENT_TOOLS)
        run_id = self._app.get(AppConfigs.RUN_ID)
        return ctools.find_path(f".tmp/rats.k8s/{run_id}")

    @apps.service(AppConfigs.RUN_ID)
    def _run_id(self) -> str:
        d = self._instance_datetime()
        return f"{d.strftime('%Y%m%d.%H.%M.%S')}.{str(uuid4())[:8]}"

    @apps.service(AppConfigs.K8S_CONFIG_CONTEXT)
    def _k8s_config_context(self) -> str:
        return os.environ.get("RATS_K8S_CONFIG_CONTEXT", "default")

    @apps.fallback_group(AppConfigs.KUSTOMIZE_IMAGES)
    def _kustomize_images(self) -> Iterator[KustomizeImage]:
        reg = os.environ.get("DEVTOOLS_IMAGE_REGISTRY", "default.local")
        project_tools = self._app.get(projects.PluginServices.PROJECT_TOOLS)
        context_hash = project_tools.image_context_hash()
        yield KustomizeImage(
            "rats-devtools",
            f"{reg}/rats-devtools",
            context_hash,
        )

    @apps.container()
    def _plugins(self) -> apps.Container:
        return apps.CompositeContainer(
            apps.PythonEntryPointContainer(self._app, "rats.k8s"),
            cli.PluginContainer(self._app),
            projects.PluginContainer(self._app),
        )

    @cache  # noqa: B019
    def _instance_datetime(self) -> datetime:
        return datetime.now()


def main() -> None:
    try:
        apps.run_plugin(logs.ConfigureApplication)
        apps.run_plugin(Application)
    except click.exceptions.ClickException as e:
        e.show()
        sys.exit(e.exit_code)
