from __future__ import annotations

import logging
import os
import shlex
import time
from collections.abc import Iterator, Mapping
from importlib import metadata
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast, final
from uuid import uuid4

import click

from rats import app_context, apps, cli, logs
from rats import projects as projects

from ._command import Command
from ._configs import AmlConfig, AmlEnvironment, AmlIO, AmlJobContext, AmlWorkspace

if TYPE_CHECKING:
    from azure.ai.ml import MLClient
    from azure.ai.ml.operations import EnvironmentOperations, JobOperations
    from azure.core.credentials import TokenCredential

logger = logging.getLogger(__name__)


@apps.autoscope
class AppConfigs:
    RUNTIME = apps.ServiceId[AmlConfig]("runtime.config")
    COMPUTE = apps.ServiceId[str]("compute.config")
    ENVIRONMENT = apps.ServiceId[AmlEnvironment]("environment.config")
    WORKSPACE = apps.ServiceId[AmlWorkspace]("workspace.config")
    JOB_CONTEXT = apps.ServiceId[AmlJobContext]("job-context.config")
    INPUTS = apps.ServiceId[AmlIO]("inputs.config-group")
    OUTPUTS = apps.ServiceId[AmlIO]("outputs.config-group")
    CONTEXT_COLLECTION = apps.ServiceId[app_context.Collection[Any]](
        "app-context-collection.config",
    )

    APP_CONTEXT = apps.ServiceId[app_context.Context[Any]]("app-context.config-group")
    """
    Service group containing context services to attach to the submitted aml job.
    """


@apps.autoscope
class AppServices:
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
    @click.option("--wait", is_flag=True, default=False, help="wait for completion of aml job.")
    def _submit(self, app_ids: tuple[str, ...], context: str, wait: bool) -> None:
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

        config = self._app.get(AppConfigs.RUNTIME)
        env_ops = self._app.get(AppServices.AML_ENVIRONMENT_OPS)
        job_ops = self._app.get(AppServices.AML_JOB_OPS)

        input_keys = config.inputs.keys()
        output_keys = config.outputs.keys()

        cmd = " && ".join(
            [
                # make sure we know the original directory
                "export RATS_AML_ORIGINAL_PWD=${PWD}",
                *[f"export RATS_AML_DATA_{k.upper()}=${{inputs.{k}}}" for k in input_keys],
                *[f"export RATS_AML_DATA_{k.upper()}=${{outputs.{k}}}" for k in output_keys],
                shlex.join(["cd", cli_command.cwd]),
                shlex.join(cli_command.args),
            ]
        )

        env_ops.create_or_update(Environment(**config.environment._asdict()))

        job = command(
            command=cmd,
            compute=config.compute,
            environment=config.environment.full_name,
            outputs={
                k: Output(type=v.type, path=v.path, mode=v.mode) for k, v in config.outputs.items()
            },
            inputs={
                k: Input(type=v.type, path=v.path, mode=v.mode) for k, v in config.inputs.items()
            },
            environment_variables={},
        )
        returned_job = job_ops.create_or_update(job)
        logger.info(f"created job: {returned_job.name}")

        while wait:
            job_details = job_ops.get(str(returned_job.name))
            logger.info(f"job {returned_job.name} status: {job_details.status}")
            job_ops.stream(str(returned_job.name))

            if job_details.status in RunHistoryConstants.TERMINAL_STATUSES:
                if job_details.status != JobStatus.COMPLETED:
                    raise RuntimeError(
                        f"job {returned_job.name} failed with status {job_details.status}",
                    )
                break

            time.sleep(2)

    @cli.command()
    @click.argument("app-ids", nargs=-1)
    @click.option("--context", default="{}")
    def _run(self, app_ids: tuple[str, ...], context: str) -> None:
        """Run one or more apps, typically in an aml job."""

        def _load_app(name: str, ctx: app_context.Collection[Any]) -> apps.AppContainer:
            entries = metadata.entry_points(group="rats.aml")
            for e in entries:
                if e.name == name:
                    return apps.AppBundle(
                        app_plugin=e.load(),
                        context=apps.StaticContainer(
                            apps.StaticProvider(
                                namespace=apps.ProviderNamespaces.SERVICES,
                                service_id=AppConfigs.CONTEXT_COLLECTION,
                                call=lambda: ctx,
                            ),
                        ),
                    )

            raise RuntimeError(f"Invalid app-id specified: {name}")

        if len(app_ids) == 0:
            logging.warning("No applications were passed to the command")

        ctx_collection = app_context.loads(context)
        for app_id in app_ids:
            app = _load_app(app_id, ctx_collection)
            app.execute()

    @apps.group(AppConfigs.APP_CONTEXT)
    def _job_context(self) -> Iterator[app_context.Context[AmlJobContext]]:
        yield app_context.Context.make(
            AppConfigs.JOB_CONTEXT,
            AmlJobContext(
                uuid=str(uuid4()),
                runtime=self._app.get(AppConfigs.RUNTIME),
                compute=self._app.get(AppConfigs.COMPUTE),
                environment=self._app.get(AppConfigs.ENVIRONMENT),
                workspace=self._app.get(AppConfigs.WORKSPACE),
            ),
        )

    @apps.fallback_service(AppConfigs.RUNTIME)
    def _runtime_config(self) -> AmlConfig:
        inputs: dict[str, AmlIO] = {}
        outputs: dict[str, AmlIO] = {}

        for inp in self._app.get_group(AppConfigs.INPUTS):
            inputs.update(inp)  # type: ignore

        for out in self._app.get_group(AppConfigs.OUTPUTS):
            outputs.update(out)  # type: ignore

        return AmlConfig(
            compute=self._app.get(AppConfigs.COMPUTE),
            inputs=inputs,
            outputs=outputs,
            workspace=self._app.get(AppConfigs.WORKSPACE),
            environment=self._app.get(AppConfigs.ENVIRONMENT),
        )

    @apps.fallback_group(AppConfigs.INPUTS)  # type: ignore
    def _inputs(self) -> Iterator[dict[str, AmlIO]]:
        from azure.ai.ml.constants import AssetTypes, InputOutputModes

        default_dataset = os.environ.get("RATS_AML_DEFAULT_INPUT_NAME")
        default_storage_account = os.environ.get("RATS_AML_DEFAULT_INPUT_STORAGE_ACCOUNT")
        default_container = os.environ.get("RATS_AML_DEFAULT_INPUT_CONTAINER")

        if not default_dataset or not default_storage_account or not default_container:
            yield {}

        yield {
            f"{default_dataset}_input": AmlIO(
                type=AssetTypes.URI_FOLDER,
                path=f"abfss://{default_container}@{default_storage_account}.dfs.core.windows.net/",
                mode=InputOutputModes.RW_MOUNT,
            ),
        }

    @apps.fallback_group(AppConfigs.OUTPUTS)  # type: ignore
    def _outputs(self) -> Iterator[Mapping[str, AmlIO]]:
        from azure.ai.ml.constants import AssetTypes, InputOutputModes

        default_dataset = os.environ.get("RATS_AML_DEFAULT_OUTPUT_NAME")
        default_storage_account = os.environ.get("RATS_AML_DEFAULT_OUTPUT_STORAGE_ACCOUNT")
        default_container = os.environ.get("RATS_AML_DEFAULT_OUTPUT_CONTAINER")

        if not default_dataset or not default_storage_account or not default_container:
            yield {}

        yield {
            f"{default_dataset}_output": AmlIO(
                type=AssetTypes.URI_FOLDER,
                path=f"abfss://{default_container}@{default_storage_account}.dfs.core.windows.net/",
                mode=InputOutputModes.RW_MOUNT,
            ),
        }

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
