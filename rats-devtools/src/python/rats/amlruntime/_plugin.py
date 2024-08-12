from pathlib import Path
from typing import cast

import click
from azure.ai.ml import MLClient
from azure.ai.ml.operations import EnvironmentOperations, JobOperations
from azure.core.credentials import TokenCredential
from azure.identity import DefaultAzureCredential

from rats import apps, cli
from rats import devtools as devtools
from rats import projects as projects

from ._commands import PluginCommands
from ._runtime import AmlRuntime, RuntimeConfig


@apps.autoscope
class _PluginConfigs:
    AML_RUNTIME = apps.ServiceId[RuntimeConfig]("aml-runtime")

    @staticmethod
    def component_runtime(name: str) -> apps.ServiceId[RuntimeConfig]:
        return apps.ServiceId[RuntimeConfig](f"{_PluginConfigs.AML_RUNTIME.name}[{name}][runtime]")


@apps.autoscope
class PluginServices:
    AML_RUNTIME = apps.ServiceId[apps.Runtime]("aml-runtime")
    AML_CLIENT = apps.ServiceId[MLClient]("aml-client")
    AML_ENVIRONMENT_OPS = apps.ServiceId[EnvironmentOperations]("aml-environment-ops")
    AML_JOB_OPS = apps.ServiceId[JobOperations]("aml-job-ops")
    COMMANDS = apps.ServiceId[cli.CommandContainer]("commands")

    MAIN_EXE = apps.ServiceId[apps.Executable]("main-exe")
    MAIN_CLICK = apps.ServiceId[click.Group]("main-click")

    CONFIGS = _PluginConfigs

    @staticmethod
    def component_runtime(name: str) -> apps.ServiceId[apps.Runtime]:
        return apps.ServiceId[apps.Runtime](f"{PluginServices.AML_RUNTIME.name}[{name}]")


class PluginContainer(apps.Container):
    _app: apps.Container

    def __init__(self, app: apps.Container) -> None:
        self._app = app

    @apps.group(devtools.PluginServices.EVENTS.OPENING)
    def _runtime_cli(self) -> apps.Executable:
        def run() -> None:
            amlruntime = self._app.get(PluginServices.MAIN_CLICK)
            parent = self._app.get(devtools.PluginServices.MAIN_CLICK)
            parent.add_command(cast(click.Command, amlruntime))

        return apps.App(run)

    @apps.service(PluginServices.MAIN_EXE)
    def _main_exe(self) -> apps.Executable:
        return apps.App(lambda: self._app.get(PluginServices.MAIN_CLICK)())

    @apps.service(PluginServices.MAIN_CLICK)
    def _main_click(self) -> click.Group:
        command_container = self._app.get(PluginServices.COMMANDS)
        amlrunner = click.Group(
            "aml-runtime",
            help="run executables and groups on AzureML",
        )
        command_container.attach(amlrunner)
        return amlrunner

    @apps.service(PluginServices.COMMANDS)
    def _commands(self) -> cli.CommandContainer:
        return PluginCommands(
            project_tools=self._app.get(projects.PluginServices.PROJECT_TOOLS),
            # on worker nodes, we always want the simple local runtime, for now.
            standard_runtime=self._app.get(apps.AppServices.STANDARD_RUNTIME),
            aml_runtime=self._app.get(PluginServices.AML_RUNTIME),
        )

    @apps.service(PluginServices.AML_RUNTIME)
    def _aml_runtime(self) -> apps.Runtime:
        return self._app.get(PluginServices.component_runtime(Path().resolve().name))

    @apps.fallback_service(PluginServices.component_runtime(Path().resolve().name))
    def _default_runtime(self) -> apps.Runtime:
        return apps.NullRuntime("No runtime configured")

    def _aml_component_runtime(self, name: str) -> AmlRuntime:
        return AmlRuntime(
            ml_client=lambda: self._app.get(PluginServices.AML_CLIENT),
            environment_operations=lambda: self._app.get(PluginServices.AML_ENVIRONMENT_OPS),
            job_operations=lambda: self._app.get(PluginServices.AML_JOB_OPS),
            config=lambda: self._app.get(PluginServices.CONFIGS.component_runtime(name)),
        )

    @apps.service(PluginServices.AML_ENVIRONMENT_OPS)
    def _aml_env_ops(self) -> EnvironmentOperations:
        return self._app.get(PluginServices.AML_CLIENT).environments

    @apps.service(PluginServices.AML_JOB_OPS)
    def _aml_job_ops(self) -> JobOperations:
        return self._app.get(PluginServices.AML_CLIENT).jobs

    @apps.service(PluginServices.CONFIGS.AML_RUNTIME)
    def _aml_runtime_config(self) -> RuntimeConfig:
        return self._app.get(PluginServices.CONFIGS.component_runtime(Path().resolve().name))

    @apps.service(PluginServices.AML_CLIENT)
    def _aml_client(self) -> MLClient:
        workspace = self._app.get(PluginServices.CONFIGS.AML_RUNTIME).workspace
        return MLClient(
            credential=cast(TokenCredential, DefaultAzureCredential()),
            subscription_id=workspace.subscription_id,
            resource_group_name=workspace.resource_group_name,
            workspace_name=workspace.workspace_name,
        )
