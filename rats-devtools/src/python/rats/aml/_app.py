from __future__ import annotations

import logging
import os
import shlex
from dataclasses import dataclass
from uuid import uuid4

import time
from collections.abc import Iterator
from importlib import metadata
from pathlib import Path
from typing import Any, TYPE_CHECKING, cast, final

import click

from rats import app_context, apps, cli, logs
from rats import projects as projects

from ._command import Command
from ._runtime import AmlEnvironment, AmlWorkspace, Runtime, RuntimeConfig

if TYPE_CHECKING:
    from azure.ai.ml import MLClient
    from azure.ai.ml.operations import EnvironmentOperations, JobOperations
    from azure.core.credentials import TokenCredential

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class _ExampleContext:
    uuid: str


@apps.autoscope
class AppConfigs:
    RUNTIME = apps.ServiceId[RuntimeConfig]("runtime.config")
    COMMAND = apps.ServiceId[Command]("command.config")
    COMPUTE = apps.ServiceId[str]("compute.config")
    ENVIRONMENT = apps.ServiceId[AmlEnvironment]("environment.config")
    WORKSPACE = apps.ServiceId[AmlWorkspace]("workspace.config")
    APP_CONTEXT = apps.ServiceId[app_context.Context[Any]]("app-context.config")


@apps.autoscope
class AppServices:
    RUNTIME = apps.ServiceId[apps.Runtime]("aml-runtime")

    AML_CLIENT = apps.ServiceId["MLClient"]("aml-client")
    AML_ENVIRONMENT_OPS = apps.ServiceId["EnvironmentOperations"]("aml-environment-ops")
    AML_JOB_OPS = apps.ServiceId["JobOperations"]("aml-job-ops")
    AML_IDENTITY = apps.ServiceId["TokenCredential"]("identity")


@final
class Application(apps.AppContainer, cli.Container, apps.PluginMixin):
    def execute(self) -> None:
        cli.create_group(click.Group("rats-aml"), self)()

    @cli.command()
    def _list(self) -> None:
        """List all the exes and groups that announce their availability to be submitted to aml."""
        entries = metadata.entry_points(group="rats.aml")
        for entry in entries:
            click.echo(entry.name)

    @cli.command()
    @click.argument("app-ids", nargs=-1)
    @click.option("--context", default='{"items": []}')
    def _submit(self, app_ids: tuple[str, ...], context: str) -> None:
        """Submit one or more apps to aml."""
        from azure.ai.ml import Input, Output, command
        from azure.ai.ml.entities import Environment
        from azure.ai.ml.operations._run_history_constants import JobStatus, RunHistoryConstants

        if len(app_ids) == 0:
            logging.warning("No applications were provided to the command")

        ptools = self._app.get(projects.PluginServices.PROJECT_TOOLS)
        ptools.build_component_image(Path.cwd().name)

        ctx = app_context.loads(context).add(
            *self._app.get_group(AppConfigs.APP_CONTEXT),
        )

        cli_command = Command(
            cwd="/opt/rats/rats-devtools",
            args=tuple(["rats-aml", "run", *app_ids, "--context", app_context.dumps(ctx)]),
            env=dict(),
        )

        cmd = " && ".join(
            [
                shlex.join(["cd", cli_command.cwd]),
                shlex.join(cli_command.args),
            ]
        )

        config = RuntimeConfig(
            command=cmd,
            env_variables=cli_command.env,
            compute=self._app.get(AppConfigs.COMPUTE),
            outputs={},
            inputs={},
            workspace=self._app.get(AppConfigs.WORKSPACE),
            environment=self._app.get(AppConfigs.ENVIRONMENT),
        )
        logger.info(f"{config.environment._asdict()}")

        env_ops = self._app.get(AppServices.AML_ENVIRONMENT_OPS)
        job_ops = self._app.get(AppServices.AML_JOB_OPS)

        env_ops.create_or_update(
            Environment(**config.environment._asdict())
        )

        job = command(
            command=config.command,
            compute=config.compute,
            environment=config.environment.full_name,
            outputs={
                k: Output(type=v.type, path=v.path, mode=v.mode) for k, v in config.outputs.items()
            },
            inputs={
                k: Input(type=v.type, path=v.path, mode=v.mode) for k, v in config.inputs.items()
            },
            environment_variables={**config.env_variables},
        )
        returned_job = job_ops.create_or_update(job)
        logger.info(f"created job: {returned_job.name}")
        job_ops.stream(str(returned_job.name))
        logger.info(f"done streaming logs: {returned_job.name}")
        while True:
            job_details = job_ops.get(str(returned_job.name))
            logger.info(f"status: {job_details.status}")
            if job_details.status in RunHistoryConstants.TERMINAL_STATUSES:
                break

            logger.warning(f"job {returned_job.name} is not done yet: {job_details.status}")
            time.sleep(2)

        if job_details.status != JobStatus.COMPLETED:
            raise RuntimeError(f"job {returned_job.name} failed with status {job_details.status}")

    @cli.command()
    @click.argument("app-ids", nargs=-1)
    @click.option("--context", default="{}")
    def _run(self, app_ids: tuple[str, ...], context: str) -> None:
        """Run one or more apps, typically in an aml job."""

        def _load_app(name: str, ctx: app_context.Collection[Any]) -> apps.AppContainer:
            entries = metadata.entry_points(group="rats.aml")
            for e in entries:
                if e.name == name:
                    return apps.AppBundle(app_plugin=e.load(), context=apps.StaticContainer(
                        apps.StaticProvider(
                            namespace=apps.ProviderNamespaces.GROUPS,
                            service_id=AppConfigs.APP_CONTEXT,
                            call=lambda: iter([ctx]),
                        ),
                    ))

            raise RuntimeError(f"Invalid app-id specified: {name}")

        if len(app_ids) == 0:
            logging.warning("No applications were passed to the command")

        ctx_collection = app_context.loads(context)
        for app_id in app_ids:
            app = _load_app(app_id, ctx_collection)
            app.execute()

    @apps.fallback_service(AppServices.RUNTIME)
    def _aml_runtime(self) -> apps.Runtime:
        """The AML Runtime of the CWD component."""
        return Runtime(
            environment_operations=lambda: self._app.get(
                AppServices.AML_ENVIRONMENT_OPS,
            ),
            job_operations=lambda: self._app.get(AppServices.AML_JOB_OPS),
            config=lambda: self._app.get(AppConfigs.RUNTIME),
        )

    @apps.fallback_service(AppConfigs.RUNTIME)
    def _runtime_config(self) -> RuntimeConfig:
        # think of this as a worker node running our executables
        command = self._app.get(AppConfigs.COMMAND)
        cmd = " && ".join(
            [
                shlex.join(["cd", command.cwd]),
                shlex.join(command.args),
            ]
        )

        return RuntimeConfig(
            command=cmd,
            env_variables=command.env,
            compute=self._app.get(AppConfigs.COMPUTE),
            outputs={},
            inputs={},
            workspace=self._app.get(AppConfigs.WORKSPACE),
            environment=self._app.get(AppConfigs.ENVIRONMENT),
        )

    @apps.fallback_service(AppConfigs.COMMAND)
    def _command_config(self) -> Command:
        return Command(
            cwd="/opt/rats/rats-devtools",
            args=tuple(["rats-aml"]),
            env=dict(),
        )

    @apps.fallback_service(AppConfigs.COMPUTE)
    def _compute_config(self) -> str:
        return os.environ["RATS_AML_COMPUTE"]

    @apps.fallback_service(AppConfigs.WORKSPACE)
    def _workspace_config(self) -> AmlWorkspace:
        return AmlWorkspace(
            subscription_id=os.environ["RATS_AML_SUBSCRIPTION_ID"],
            resource_group_name=os.environ["RATS_AML_RESOURCE_GROUP"],
            workspace_name=os.environ["RATS_AML_WORKSPACE"],
        )

    @apps.fallback_service(AppConfigs.ENVIRONMENT)
    def _environment_config(self) -> AmlEnvironment:
        ptools = self._app.get(projects.PluginServices.PROJECT_TOOLS)
        component_name = Path.cwd().name
        image = ptools.container_image(component_name)

        return AmlEnvironment(
            name=Path.cwd().name,
            image=image.full,
            version=image.tag,
        )

    @apps.fallback_service(AppServices.AML_ENVIRONMENT_OPS)
    def _aml_env_ops(self) -> EnvironmentOperations:
        return self._app.get(AppServices.AML_CLIENT).environments

    @apps.service(AppServices.AML_JOB_OPS)
    def _aml_job_ops(self) -> JobOperations:
        return self._app.get(AppServices.AML_CLIENT).jobs

    @apps.fallback_service(AppServices.AML_CLIENT)
    def _aml_client(self) -> MLClient:
        from azure.ai.ml import MLClient

        workspace = self._app.get(AppConfigs.RUNTIME).workspace
        return MLClient(
            credential=self._app.get(AppServices.AML_IDENTITY),
            subscription_id=workspace.subscription_id,
            resource_group_name=workspace.resource_group_name,
            workspace_name=workspace.workspace_name,
        )

    @apps.fallback_service(AppServices.AML_IDENTITY)
    def _aml_identity(self) -> TokenCredential:
        from azure.identity import DefaultAzureCredential

        return cast("TokenCredential", DefaultAzureCredential())

    @apps.fallback_group(AppConfigs.APP_CONTEXT)
    def _default_context(self) -> Iterator[app_context.Context[_ExampleContext]]:
        yield app_context.Context.make(apps.ServiceId("foo"), _ExampleContext(str(uuid4())))
        yield app_context.Context.make(apps.ServiceId("foo"), _ExampleContext(str(uuid4())))

    @apps.container()
    def _plugins(self) -> apps.Container:
        return apps.CompositeContainer(
            apps.PythonEntryPointContainer(self._app, "rats.aml"),
            projects.PluginContainer(self._app),
        )


def main() -> None:
    """Main entry-point to the `rats-aml` cli command."""
    apps.run_plugin(logs.ConfigureApplication)
    apps.run_plugin(Application)
