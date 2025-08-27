import json
import logging
import os
import subprocess
import sys
from collections.abc import Collection, Iterator
from datetime import datetime
from functools import cache
from importlib import resources
from pathlib import Path
from typing import Any
from uuid import uuid4

import click
import yaml
from kubernetes import client, config

from rats import app_context as app_context
from rats import apps as apps
from rats import cli as cli
from rats import logs as logs
from rats import projects
from rats_resources import k8s

from ._kustomize import KustomizeImage
from ._workflow_jobs import CreateNamespace, KustomizeBuild

logger = logging.getLogger(__name__)


@apps.autoscope
class AppConfigs:
    K8S_CONFIG_CONTEXT = apps.ServiceId[str]("k8s-config-context.config")
    APP_CONTEXT = apps.ServiceId[app_context.Context[Any]]("app-context.config-group.config")
    """Service group containing context services to attach to the submitted k8s process."""
    RUN_ID = apps.ServiceId[str]("run-id.config")
    KUSTOMIZE_IMAGES = apps.ServiceId[KustomizeImage]("kustomize-images.config")
    RUNNABLE_APP_IDS = apps.ServiceId[str]("runnable-app-ids.config")
    APP_IDS = apps.ServiceId[Collection[str]]("app-ids.config")


@apps.autoscope
class AppServices:
    RESOURCE_PATH = apps.ServiceId[Path]("resource-path")
    RUN_STAGING_PATH = apps.ServiceId[Path]("run-staging-path")
    RUN_DATETIME = apps.ServiceId[datetime]("run-datetime")
    CTX_COLLECTION = apps.ServiceId[app_context.Collection]("ctx-collection")


class Application(apps.AppContainer, cli.Container, apps.PluginMixin):
    _app_ids: tuple[str, ...]
    _ctx_collection: app_context.Collection

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

        runtime_apps = list(self._app.get_group(AppConfigs.RUNNABLE_APP_IDS))
        for a in app_ids:
            # make sure all these app ids are valid
            if a not in runtime_apps:
                raise RuntimeError(f"app id not found: {a}")

        self._ctx_collection = ctx_collection
        self._app_ids = app_ids

        staging_path = self._app.get(AppServices.RUN_STAGING_PATH)
        staging_path.mkdir(parents=True, exist_ok=False)

        self._customize_build().execute()

        built = subprocess.run(
            ["kubectl", "kustomize"],
            check=True,
            text=True,
            cwd=staging_path,
            capture_output=True,
        ).stdout
        logger.info(f"completed kustomize build\n{built}")

    @cache
    def _customize_build(self) -> apps.Executable:
        ctools = self._app.get(projects.PluginServices.CWD_COMPONENT_TOOLS)
        return KustomizeBuild(
            ctools=ctools,
            run_id=self._app.get(AppConfigs.RUN_ID),
            resource_path=self._app.get(AppServices.RESOURCE_PATH),
            staging_path=self._app.get(AppServices.RUN_STAGING_PATH),
            images=list(self._app.get_group(AppConfigs.KUSTOMIZE_IMAGES)),
            main_component=ctools.component_name(),
            app_ids=self._app.get(AppConfigs.APP_IDS),
            ctx_collection=self._app.get(AppServices.CTX_COLLECTION),
        )

    @apps.fallback_group(AppConfigs.RUNNABLE_APP_IDS)
    def _runtime_list(self) -> Iterator[str]:
        response = subprocess.run(["rats-runtime", "list"], capture_output=True)
        yield from tuple(response.stdout.decode("UTF-8").splitlines())

    @apps.fallback_service(AppServices.RUN_STAGING_PATH)
    def _run_staging_path(self) -> Path:
        ctools = self._app.get(projects.PluginServices.CWD_COMPONENT_TOOLS)
        run_id = self._app.get(AppConfigs.RUN_ID)
        return ctools.find_path(f".tmp/rats.k8s/{run_id}")

    @apps.service(AppConfigs.RUN_ID)
    def _run_id(self) -> str:
        d = self._app.get(AppServices.RUN_DATETIME)
        return f"{d.strftime('%Y%m%d.%H.%M.%S')}.{str(uuid4())[:8]}"

    @apps.service(AppConfigs.K8S_CONFIG_CONTEXT)
    def _k8s_config_context(self) -> str:
        return os.environ.get("RATS_K8S_CONFIG_CONTEXT", "default")

    @apps.fallback_group(AppConfigs.KUSTOMIZE_IMAGES)
    def _kustomize_images(self) -> Iterator[KustomizeImage]:
        """By default, we make available any discovered component to k8s."""
        reg = os.environ.get("DEVTOOLS_IMAGE_REGISTRY", "default.local")
        project_tools: projects.ProjectTools = self._app.get(projects.PluginServices.PROJECT_TOOLS)
        context_hash = project_tools.image_context_hash()
        for component in project_tools.discover_components():
            yield KustomizeImage(
                component.name,
                f"{reg}/{component.name}",
                context_hash,
            )

    @apps.service(AppConfigs.APP_IDS)
    def _run_app_ids(self) -> Collection[str]:
        return self._app_ids

    @apps.service(AppServices.CTX_COLLECTION)
    def _run_ctx_collection(self) -> app_context.Collection:
        return self._ctx_collection

    @apps.service(AppServices.RUN_DATETIME)
    def _instance_datetime(self) -> datetime:
        return datetime.now()

    @apps.fallback_service(AppServices.RESOURCE_PATH)
    def _resource_path(self) -> Path:
        with resources.path(k8s, "workflow-jobs") as p:
            return p.resolve()

    @apps.container()
    def _plugins(self) -> apps.Container:
        return apps.CompositeContainer(
            apps.PythonEntryPointContainer(self._app, "rats.k8s"),
            cli.PluginContainer(self._app),
            projects.PluginContainer(self._app),
        )


def main() -> None:
    try:
        apps.run_plugin(logs.ConfigureApplication)
        apps.run_plugin(Application)
    except click.exceptions.ClickException as e:
        e.show()
        sys.exit(e.exit_code)
