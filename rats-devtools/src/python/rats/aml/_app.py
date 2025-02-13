import json
import logging
import os
from pathlib import Path
from typing import Iterator, cast, final

import click
from rats import apps, cli, logs, projects, stdruntime
from rats.aml._runtime import AmlEnvironment, AmlWorkspace, Runtime, RuntimeConfig

logger = logging.getLogger(__name__)


@apps.autoscope
class AppConfigs:
    RUNTIME = apps.ServiceId[RuntimeConfig]("runtime.config")
    EXE_GROUP = apps.ServiceId[apps.ServiceId[apps.Executable]]("exe-group.config")


@apps.autoscope
class AppServices:
    RUNTIME = apps.ServiceId[apps.Runtime]("aml-runtime")
    HELLO_WORLD = apps.ServiceId[apps.Executable]("hello-world")

    AML_CLIENT = apps.ServiceId["MLClient"]("aml-client")  # type: ignore[reportUndefinedVariable]
    AML_ENVIRONMENT_OPS = apps.ServiceId["EnvironmentOperations"]("aml-environment-ops")  # type: ignore[reportUndefinedVariable]
    AML_JOB_OPS = apps.ServiceId["JobOperations"]("aml-job-ops")  # type: ignore[reportUndefinedVariable]


@final
class Application(apps.AppContainer, cli.Container, apps.PluginMixin):
    def execute(self) -> None:
        cli.create_group(click.Group("rats-aml"), self)()

    @cli.command()
    def _list(self) -> None:
        """List all the exes and groups that announce their availability to be submitted to aml."""
        for exe in self._app.get_group(AppConfigs.EXE_GROUP):
            click.echo(exe.name)

    @cli.command()
    @click.option("--exe-id", multiple=True)
    @click.option("--group-id", multiple=True)
    def _submit(self, exe_id: tuple[str, ...], group_id: tuple[str, ...]) -> None:
        """Submit one or more exes and groups to aml."""
        if len(exe_id) == 0 and len(group_id) == 0:
            raise ValueError("No executables or groups were passed to the command")

        ptools = self._app.get(projects.PluginServices.PROJECT_TOOLS)
        ptools.build_component_image(Path.cwd().name)

        exes = [apps.ServiceId[apps.Executable](exe) for exe in exe_id]
        groups = [apps.ServiceId[apps.Executable](group) for group in group_id]

        runtime = self._app.get(AppServices.RUNTIME)

        # we can join these into one job later if needed
        if len(exes):
            runtime.execute(*exes)

        if len(groups):
            runtime.execute_group(*groups)

    @cli.command()
    def _worker_node(self) -> None:
        """
        Run the worker node process.

        This command is intended to be run in an aml job. It will execute any exes and groups
        that are passed to it through environment variables.
        """
        runtime = self._app.get(stdruntime.PluginServices.STANDARD_RUNTIME)
        exe_ids = json.loads(
            os.environ.get("DEVTOOLS_AMLRUNTIME_EXE_IDS", "[]"),
            object_hook=lambda d: apps.ServiceId[apps.Executable](**d),
        )
        group_ids = json.loads(
            os.environ.get("DEVTOOLS_AMLRUNTIME_EVENT_IDS", "[]"),
            object_hook=lambda d: apps.ServiceId[apps.Executable](**d),
        )

        runtime.execute(*exe_ids)
        runtime.execute_group(*group_ids)

    @apps.fallback_service(AppServices.RUNTIME)
    def _aml_runtime(self) -> apps.Runtime:
        """The AML Runtime of the CWD component."""
        component_tools = self._app.get(projects.PluginServices.CWD_COMPONENT_TOOLS)
        return Runtime(
            environment_operations=lambda: self._app.get(
                AppServices.AML_ENVIRONMENT_OPS,
            ),
            job_operations=lambda: self._app.get(AppServices.AML_JOB_OPS),
            config=lambda: self._app.get(AppConfigs.RUNTIME),
        )

    @apps.fallback_service(AppServices.AML_ENVIRONMENT_OPS)
    def _aml_env_ops(self) -> "EnvironmentOperations":  # type: ignore[reportUndefinedVariable]  # noqa: F821
        return self._app.get(AppServices.AML_CLIENT).environments

    @apps.service(AppServices.AML_JOB_OPS)
    def _aml_job_ops(self) -> "JobOperations":  # type: ignore[reportUndefinedVariable]  # noqa: F821
        return self._app.get(AppServices.AML_CLIENT).jobs

    @apps.fallback_service(AppServices.AML_CLIENT)
    def _aml_client(self) -> "MLClient":  # type: ignore[reportUndefinedVariable]  # noqa: F821
        from azure.ai.ml import MLClient
        from azure.core.credentials import TokenCredential
        from azure.identity import DefaultAzureCredential

        workspace = self._app.get(AppConfigs.RUNTIME).workspace
        return MLClient(
            credential=cast(TokenCredential, DefaultAzureCredential()),
            subscription_id=workspace.subscription_id,
            resource_group_name=workspace.resource_group_name,
            workspace_name=workspace.workspace_name,
        )

    @apps.fallback_service(AppConfigs.RUNTIME)
    def _devtools_runtime_config(self) -> RuntimeConfig:
        # think of this as a worker node running our executables
        project_config = self._app.get(projects.PluginServices.CONFIGS.PROJECT)
        ptools = self._app.get(projects.PluginServices.PROJECT_TOOLS)
        component_name = Path.cwd().name
        image = ptools.container_image(component_name)

        cmd = " && ".join([
            "cd /opt/rats/rats-devtools",
            "rats-aml",
        ])

        # a lot more of this needs to be configurable
        return RuntimeConfig(
            command=cmd,
            env_variables=dict(),
            compute=os.environ["DEVTOOLS_AMLRUNTIME_COMPUTE"],
            outputs={},
            inputs={},
            workspace=AmlWorkspace(
                subscription_id=os.environ["DEVTOOLS_AMLRUNTIME_SUBSCRIPTION_ID"],
                resource_group_name=os.environ["DEVTOOLS_AMLRUNTIME_RESOURCE_GROUP"],
                workspace_name=os.environ["DEVTOOLS_AMLRUNTIME_WORKSPACE"],
            ),
            environment=AmlEnvironment(
                name=Path.cwd().name,
                image=image.full,
                version=image.tag,
            ),
        )

    @apps.fallback_group(AppConfigs.EXE_GROUP)
    def _default_exes(self) -> Iterator[apps.ServiceId[apps.Executable]]:
        yield AppServices.HELLO_WORLD

    @apps.container()
    def _plugins(self) -> apps.Container:
        return apps.CompositeContainer(
            apps.PythonEntryPointContainer(self._app, "rats.aml"),
            projects.PluginContainer(self._app),
        )


def main() -> None:
    """
    Main entry-point to the `rats-aml` cli command.
    """
    apps.run_plugin(logs.ConfigureApplication)
    apps.run_plugin(Application)
