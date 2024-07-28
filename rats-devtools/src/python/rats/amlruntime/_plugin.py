import os
from typing import cast

import click
from azure.ai.ml import MLClient
from azure.ai.ml.operations import EnvironmentOperations, JobOperations
from azure.core.credentials import TokenCredential
from azure.identity import DefaultAzureCredential

from rats import apps, cli
from rats import devtools as devtools

from ._commands import PluginCommands
from ._runtime import AmlEnvironment, AmlRuntime, AmlWorkspace, RuntimeConfig


@apps.autoscope
class _PluginClickServices:
    GROUP = apps.ServiceId[click.Group]("group")


@apps.autoscope
class _PluginConfigs:
    AML_RUNTIME = apps.ConfigId[RuntimeConfig]("aml-runtime")


@apps.autoscope
class PluginServices:
    AML_RUNTIME = apps.ServiceId[AmlRuntime]("aml-runtime")
    AML_CLIENT = apps.ServiceId[MLClient]("aml-client")
    AML_ENVIRONMENT_OPS = apps.ServiceId[EnvironmentOperations]("aml-environment-ops")
    AML_JOB_OPS = apps.ServiceId[JobOperations]("aml-job-ops")
    COMMANDS = apps.ServiceId[cli.CommandContainer]("commands")

    CLICK = _PluginClickServices
    CONFIGS = _PluginConfigs


class PluginContainer(apps.Container):
    _app: apps.Container

    def __init__(self, app: apps.Container) -> None:
        self._app = app

    @apps.group(cli.PluginServices.EVENTS.command_open(cli.PluginServices.ROOT_COMMAND))
    def _runner_cli(self) -> apps.Executable:
        def run() -> None:
            group = self._app.get(
                cli.PluginServices.click_command(cli.PluginServices.ROOT_COMMAND)
            )
            amlrunner = self._app.get(PluginServices.CLICK.GROUP)
            self._app.get(PluginServices.COMMANDS).on_group_open(amlrunner)
            group.add_command(cast(click.Command, amlrunner))

        return apps.App(run)

    @apps.service(PluginServices.CLICK.GROUP)
    def _click_group(self) -> click.Group:
        return click.Group(
            "aml-runner",
            help="submit executables and events to aml",
        )

    @apps.service(PluginServices.COMMANDS)
    def _commands(self) -> cli.CommandContainer:
        return PluginCommands(
            project_tools=self._app.get(devtools.PluginServices.PROJECT_TOOLS),
            # on worker nodes, we always want the simple local runtime, for now.
            worker_node_runtime=self._app.get(apps.AppServices.STANDARD_RUNTIME),
            aml_runtime=self._app.get(PluginServices.AML_RUNTIME),
        )

    @apps.service(PluginServices.AML_RUNTIME)
    def _aml_runtime(self) -> AmlRuntime:
        return AmlRuntime(
            ml_client=lambda: self._app.get(PluginServices.AML_CLIENT),
            environment_operations=lambda: self._app.get(PluginServices.AML_ENVIRONMENT_OPS),
            job_operations=lambda: self._app.get(PluginServices.AML_JOB_OPS),
            config=lambda: self._app.get(PluginServices.CONFIGS.AML_RUNTIME),
        )

    @apps.service(PluginServices.AML_ENVIRONMENT_OPS)
    def _aml_env_ops(self) -> EnvironmentOperations:
        return self._app.get(PluginServices.AML_CLIENT).environments

    @apps.service(PluginServices.AML_JOB_OPS)
    def _aml_job_ops(self) -> JobOperations:
        return self._app.get(PluginServices.AML_CLIENT).jobs

    @apps.service(PluginServices.AML_CLIENT)
    def _aml_client(self) -> MLClient:
        workspace = self._app.get(PluginServices.CONFIGS.AML_RUNTIME).workspace
        return MLClient(
            credential=cast(TokenCredential, DefaultAzureCredential()),
            subscription_id=workspace.subscription_id,
            resource_group_name=workspace.resource_group_name,
            workspace_name=workspace.workspace_name,
        )

    @apps.service(PluginServices.CONFIGS.AML_RUNTIME)
    def _aml_runtime_config(self) -> RuntimeConfig:
        # think of this as a worker node running our executables
        reg = os.environ.get("DEVTOOLS_K8S_IMAGE_REGISTRY", "default.local")
        project_tools = self._app.get(devtools.PluginServices.PROJECT_TOOLS)
        active_component = self._app.get(devtools.PluginServices.ACTIVE_COMPONENT_OPS)
        name = active_component.find_path(".").name
        context_hash = project_tools.image_context_hash()

        image = f"{reg}/{name}:{context_hash}"

        return RuntimeConfig(
            command=os.environ.get(
                "DEVTOOLS_AMLRUNTIME_COMMAND",
                "rats-devtools aml-runner worker-node",
            ),
            compute=os.environ.get("DEVTOOLS_AMLRUNTIME_COMPUTE", "default"),
            workspace=AmlWorkspace(
                subscription_id=os.environ.get("DEVTOOLS_AMLRUNTIME_SUBSCRIPTION_ID", ""),
                resource_group_name=os.environ.get("DEVTOOLS_AMLRUNTIME_RESOURCE_GROUP", ""),
                workspace_name=os.environ.get("DEVTOOLS_AMLRUNTIME_WORKSPACE", "default"),
            ),
            environment=AmlEnvironment(
                name=name,
                image=image,
                version=context_hash,
            ),
        )
