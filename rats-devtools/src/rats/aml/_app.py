from __future__ import annotations

import logging
import os
import shlex
import sys
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
from ._configs import AmlEnvironment, AmlIO, AmlJobContext, AmlJobDetails, AmlWorkspace

if TYPE_CHECKING:
    from azure.ai.ml import MLClient
    from azure.ai.ml.operations import EnvironmentOperations, JobOperations
    from azure.core.credentials import TokenCredential

logger = logging.getLogger(__name__)


@apps.autoscope
class AppConfigs:
    """
    Configuration services and groups used by the [rats.aml.Application][].

    Some of these config services and groups alter the construction of the services defined in
    [AppServices][rats.aml.AppServices].
    """

    JOB_DETAILS = apps.ServiceId[AmlJobDetails]("job-details.config")
    """
    Aml job runtime information containing compute, input/output, workspace, and environment info.

    This service defers to more specific configurations that can be defined individually if you
    don't require providing the entire configuration.

    ```python
    class Plugin(apps.Container):

        @apps.service(AppConfigs.JOB_DETAILS)
        def _runtime(self) -> AmlConfig:
            AmlConfig(
                compute="[compute-cluster-name]",
                inputs={},
                outputs={},
                workspace=self._app.get(AppConfigs.WORKSPACE),
                environment=self._app.get(AppConfigs.ENVIRONMENT),
            )
    ```
    """

    COMPUTE = apps.ServiceId[str]("compute.config")
    """
    The name of the compute cluster the aml job should be submitted to.

    This can be a full resource id in cases where the cluster is part of a workspace other than the
    one being submitted to.
    """

    ENVIRONMENT = apps.ServiceId[AmlEnvironment]("environment.config")
    """
    The workspace environment that should be created and used for the aml job.

    If the environment already exists, it will be updated before submitting the job. We recommend
    using an environment that leverages a pre-built container image and not relying on aml to
    upload your code and build a new container on each job submission. This allows you to rely on
    images that you've ideally built and tested in CI pipelines without modification.
    """

    WORKSPACE = apps.ServiceId[AmlWorkspace]("workspace.config")
    """The workspace information for submitting aml jobs into."""

    COMMAND_KWARGS = apps.ServiceId[Mapping[str, Any]]("command-kwargs.config")
    """
    Additional arguments to be added to the [azure.ai.ml.command][] call when submitting a job.

    In cases where the [rats.aml][] module does not provide the desired configuration for a job,
    this service can be used to add a dictionary of kwargs that will be added to the command
    construction function without validation.

    ```python
    class Plugin(apps.Container):
        @apps.service(AppConfigs.COMMAND_KWARGS)
        def _ml_command_kwargs(self) -> Mapping[str, Any]:
            return {
                "resources": {"instance_count": 1},
            }
    ```
    """

    JOB_CONTEXT = apps.ServiceId[AmlJobContext]("job-context.config")
    """
    Context element containing basic job information and always shared with the worker node.

    This context object is always added to any registered
    [rats.aml.AppConfigs.CONTEXT_COLLECTION][] in order to provide a handful of details that might
    be useful for tracking larger pipelines.
    """

    INPUTS = apps.ServiceId[Mapping[str, AmlIO]]("inputs.config-group")
    """
    Aml inputs used by the job and mounted on the worker nodes.

    On the worker node, the path to the mounted input directory is exposed as an environment
    variable prefixed with `RATS_AML_PATH_`, followed by the uppercase `[input-name]`. So an
    input registered like below, and named `model_input` will have an environment variable
    `RATS_AML_PATH_MODEL_INPUT` containing the local path to the mounted directory/file.

    ```python
    class Plugin(apps.Container):
        @apps.fallback_group(AppConfigs.INPUTS)
        def _inputs(self) -> Iterator[Mapping[str, AmlIO]]:
            from azure.ai.ml.constants import AssetTypes, InputOutputModes

            yield {
                f"[input-name]": AmlIO(
                    type=AssetTypes.URI_FOLDER,
                    path=f"abfss://[container]@[storage-account].dfs.core.windows.net/[path]",
                    mode=InputOutputModes.RW_MOUNT,
                ),
            }
    ```
    """
    OUTPUTS = apps.ServiceId[Mapping[str, AmlIO]]("outputs.config-group")
    """
    Aml outputs used by the job and mounted on the worker nodes.

    On the worker node, the path to the mounted output directory is exposed as an environment
    variable prefixed with `RATS_AML_PATH_`, followed by the uppercase `[output-name]`. So an
    output registered like below, and named `model_output` will have an environment variable
    `RATS_AML_PATH_MODEL_OUTPUT` containing the local path to the mounted directory/file.

    ```python
    class Plugin(apps.Container):
        @apps.fallback_group(AppConfigs.OUTPUTS)
        def _outputs(self) -> Iterator[Mapping[str, AmlIO]]:
            from azure.ai.ml.constants import AssetTypes, InputOutputModes

            yield {
                f"[output-name]": AmlIO(
                    type=AssetTypes.URI_FOLDER,
                    path=f"abfss://[container]@[storage-account].dfs.core.windows.net/[path]",
                    mode=InputOutputModes.RW_MOUNT,
                ),
            }
    ```
    """
    CONTEXT_COLLECTION = apps.ServiceId[app_context.Collection[Any]]("app-ctx-collection.config")
    """
    Collection containing the entire context being sent to the aml job.

    You should not set this service config directly and instead register to the
    [rats.aml.AppConfigs.APP_CONTEXT][] service group to add elements to this collection. You can
    retrieve this service config on the aml job instance to retrieve the registered contexts.

    ```python
    class Application(apps.AppContainer):
        def execute(self) -> None:
            context_collection = self._app.get(aml.AppConfigs.CONTEXT_COLLECTION)
            print("loaded context:")
            for item in context_collection.items:
                print(f"{item.service_id} -> {item.values}")
    ```
    """

    CLI_ENVS = apps.ServiceId[Mapping[str, str]]("cli-envs.config-group")
    """
    Dictionaries to merge and attach as environment variables to the submitted aml job.

    The special environment variables like `RATS_AML_RUN_CONTEXT` are not affected by the
    definition of these service groups.

    ```python
    class Plugin(apps.Container):

        @apps.service_group(AppConfigs.CLI_ENVS)
        def _envs(self) -> Iterator[Mapping[str, str]]:
            yield {"MY_JOB_ENV": "some-useful-information"}
    ```
    """

    CLI_CWD = apps.ServiceId[str]("cli-cwd.config")
    """
    The directory within the aml job container image from where to run the `rats-aml run` command.

    This defaults to the directory of the component `rats-aml` is being run from, assuming the
    container has been built with this component at `/opt/<project>/<component>`, as is done in
    the `Containerfile`'s in this repository. Define this config service if this convention doesn't
    match your project's.
    """

    APP_CONTEXT = apps.ServiceId[app_context.Context[Any]]("app-context.config-group")
    """
    Service group containing context services to attach to the submitted aml job.

    By default, [rats.aml.AppConfigs.JOB_CONTEXT][] is attached and provides some basic information
    about the submitted job along with a unique id that can be used for tracking runs.
    """


@apps.autoscope
class AppServices:
    """
    Service classes used and exposed by [rats.aml.Application][].

    Many of the constructor arguments for these services are configurable by providing config
    services and groups defined in [AppConfigs][rats.aml.AppConfigs]. Any service that isn't
    configurable to the extent needed can typically be overwritten by the user in a plugin
    container.
    """

    AML_CLIENT = apps.ServiceId["MLClient"]("aml-client")
    """Instance of the [azure.ai.ml.MLClient][] used to submit this application's aml jobs."""

    AML_ENVIRONMENT_OPS = apps.ServiceId["EnvironmentOperations"]("aml-environment-ops")
    """
    [azure.ai.ml.operations.EnvironmentOperations][] used to create and update the aml environment.

    This service is not overwritable because it comes directly from the aml client defined by
    [AppServices.AML_CLIENT][rats.aml.AppServices.AML_CLIENT].
    """

    AML_JOB_OPS = apps.ServiceId["JobOperations"]("aml-job-ops")
    """
    [azure.ai.ml.operations.JobOperations][] used to submit and monitor the aml job for completion.

    This service is not overwritable because it comes directly from the aml client defined by
    [AppServices.AML_CLIENT][rats.aml.AppServices.AML_CLIENT].
    """
    AML_IDENTITY = apps.ServiceId["TokenCredential"]("identity")
    """
    [azure.core.credentials.TokenCredential][] used by the MLClient.

    By default, we use a DefaultAzureCredential, but a more specific one can be used in more
    advanced projects.
    """


@final
class _CliContext(apps.Container):
    SERVICE_ID = apps.ServiceId[tuple[str, ...]]("rats.aml:argv")

    def __init__(self, argv: tuple[str, ...]) -> None:
        self._argv = argv

    @apps.service(SERVICE_ID)
    def _provider(self) -> tuple[str, ...]:
        return self._argv


@final
class Application(apps.AppContainer, cli.Container, apps.PluginMixin):
    """CLI application for submitting rats applications to be run on aml."""

    def execute(self) -> None:
        """Runs the `rats-aml` cli that provides methods for listing and submitting aml jobs."""
        argv = self._app.get(_CliContext.SERVICE_ID)
        cli.create_group(click.Group("rats-aml"), self).main(
            args=argv[1:],
            prog_name=Path(argv[0]).name,
            auto_envvar_prefix="RATS_AML",
            # don't end the process
            standalone_mode=False,
        )

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

        for a in app_ids:
            # make sure all these app ids are valid
            self._find_app(a)

        ctx = app_context.loads(context).add(
            *self._app.get_group(AppConfigs.APP_CONTEXT),
        )

        env = {}
        for env_map in self._app.get_group(AppConfigs.CLI_ENVS):
            env.update(env_map)

        cli_command = Command(
            cwd=self._app.get(AppConfigs.CLI_CWD),
            args=tuple(["rats-aml", "run", *app_ids]),
            env=env,
        )

        config = self._app.get(AppConfigs.JOB_DETAILS)
        env_ops = self._app.get(AppServices.AML_ENVIRONMENT_OPS)
        job_ops = self._app.get(AppServices.AML_JOB_OPS)

        input_keys = config.inputs.keys()
        output_keys = config.outputs.keys()

        cmd = " && ".join(
            [
                # make sure we know the original directory and any input/output paths
                "export RATS_AML_ORIGINAL_PWD=${PWD}",
                *[f"export RATS_AML_PATH_{k.upper()}=${{inputs.{k}}}" for k in input_keys],
                *[f"export RATS_AML_PATH_{k.upper()}=${{outputs.{k}}}" for k in output_keys],
                shlex.join(["cd", cli_command.cwd]),
                shlex.join(cli_command.args),
            ]
        )

        env_ops.create_or_update(Environment(**config.environment._asdict()))

        extra_aml_command_args = self._app.get(AppConfigs.COMMAND_KWARGS)

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
            environment_variables={
                **cli_command.env,
                "RATS_AML_RUN_CONTEXT": app_context.dumps(ctx),
            },
            **extra_aml_command_args,
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
            return apps.AppBundle(
                app_plugin=self._find_app(name),
                context=apps.StaticContainer(
                    apps.StaticProvider(
                        namespace=apps.ProviderNamespaces.SERVICES,
                        service_id=AppConfigs.CONTEXT_COLLECTION,
                        call=lambda: ctx,
                    ),
                ),
            )

        if len(app_ids) == 0:
            logging.warning("No applications were passed to the command")

        ctx_collection = app_context.loads(context)
        for app_id in app_ids:
            app = _load_app(app_id, ctx_collection)
            app.execute()

    def _find_app(self, name: str) -> type[apps.AppContainer]:
        entries = metadata.entry_points(group="rats.aml.apps")
        for e in entries:
            if e.name == name:
                return e.load()

        raise RuntimeError(f"AML app-id not found: {name}")

    @apps.fallback_service(AppConfigs.CLI_CWD)
    def _cwd(self) -> str:
        pconfig = self._app.get(projects.PluginServices.CONFIGS.PROJECT)
        component_name = Path.cwd().name
        return f"/opt/{pconfig.name}/{component_name}"

    @apps.fallback_group(AppConfigs.CLI_ENVS)
    def _default_envs(self) -> Iterator[Mapping[str, str]]:
        yield {"RATS_AML_DEFAULT_ENV": "example"}

    @apps.group(AppConfigs.APP_CONTEXT)
    def _job_context(self) -> Iterator[app_context.Context[AmlJobContext]]:
        yield app_context.Context.make(
            AppConfigs.JOB_CONTEXT,
            AmlJobContext(
                uuid=str(uuid4()),
                job_details=self._app.get(AppConfigs.JOB_DETAILS),
            ),
        )

    @apps.fallback_service(AppConfigs.JOB_DETAILS)
    def _runtime_config(self) -> AmlJobDetails:
        inputs: dict[str, AmlIO] = {}
        outputs: dict[str, AmlIO] = {}

        for inp in self._app.get_group(AppConfigs.INPUTS):
            inputs.update(inp)

        for out in self._app.get_group(AppConfigs.OUTPUTS):
            outputs.update(out)

        return AmlJobDetails(
            compute=self._app.get(AppConfigs.COMPUTE),
            inputs=inputs,
            outputs=outputs,
            workspace=self._app.get(AppConfigs.WORKSPACE),
            environment=self._app.get(AppConfigs.ENVIRONMENT),
        )

    @apps.fallback_service(AppConfigs.COMMAND_KWARGS)
    def _aml_cmd_kwargs(self) -> Mapping[str, Any]:
        return {}

    @apps.fallback_group(AppConfigs.INPUTS)
    def _inputs(self) -> Iterator[Mapping[str, AmlIO]]:
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

    @apps.fallback_group(AppConfigs.OUTPUTS)
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

        workspace = self._app.get(AppConfigs.JOB_DETAILS).workspace
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

    @apps.fallback_service(_CliContext.SERVICE_ID)
    def _default_args(self) -> tuple[str, ...]:
        return tuple(sys.argv)

    @apps.container()
    def _plugins(self) -> apps.Container:
        return apps.CompositeContainer(
            apps.PythonEntryPointContainer(self._app, "rats.aml"),
            projects.PluginContainer(self._app),
        )


def submit(
    *app_ids: str,
    context: app_context.Collection[Any] = app_context.EMPTY_COLLECTION,
    wait: bool = False,
) -> None:
    """
    Submit an AML job programmatically instead of calling `rats-aml submit`.

    Args:
        app_ids: list of the application to run on the remote aml job as found in pyproject.toml
        context: context to send to the remote aml job
        wait: wait for the successful completion of the submitted aml job.
    """
    w = ["--wait"] if wait else []
    cmd = (
        "rats-aml",
        "submit",
        *app_ids,
        "--context",
        app_context.dumps(context),
        *w,
    )
    submitter = apps.AppBundle(
        app_plugin=Application,
        context=_CliContext(cmd),
    )
    submitter.execute()


def main() -> None:
    """Main entry-point to the `rats-aml` cli command."""
    apps.run_plugin(logs.ConfigureApplication)
    apps.run_plugin(Application)
