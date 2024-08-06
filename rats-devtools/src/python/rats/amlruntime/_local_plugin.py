"""This is the plugin that should only be enabled when locally developing rats."""

import os
from pathlib import Path
from typing import cast

from azure.ai.ml import MLClient
from azure.core.credentials import TokenCredential
from azure.identity import DefaultAzureCredential

from rats import apps, cli
from rats import projects as projects

from ._commands import PluginCommands
from ._plugin import PluginServices
from ._runtime import AmlEnvironment, AmlRuntime, AmlWorkspace, RuntimeConfig


class PluginContainer(apps.Container):
    _app: apps.Container

    def __init__(self, app: apps.Container) -> None:
        self._app = app

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
        try:
            return self._app.get(PluginServices.component_runtime(Path().resolve().name))
        except apps.ServiceNotFoundError as e:
            if e.service_id == PluginServices.component_runtime(Path().resolve().name):
                # this api is confusing
                return apps.NullRuntime()
            raise

    @apps.service(PluginServices.component_runtime("rats-devtools"))
    def _devtools_runtime(self) -> AmlRuntime:
        return self._aml_component_runtime("rats-devtools")

    @apps.service(PluginServices.component_runtime("rats-examples-datasets"))
    def _datasets_runtime(self) -> AmlRuntime:
        return self._aml_component_runtime("rats-examples-datasets")

    @apps.service(PluginServices.CONFIGS.component_runtime("rats-devtools"))
    def _devtools_runtime_config(self) -> RuntimeConfig:
        return self._component_aml_runtime_config("rats-devtools")

    @apps.service(PluginServices.CONFIGS.component_runtime("rats-examples-datasets"))
    def _datasets_runtime_config(self) -> RuntimeConfig:
        return self._component_aml_runtime_config("rats-examples-datasets")

    @apps.service(PluginServices.CONFIGS.component_runtime("rats-examples-minimal"))
    def _minimal_runtime_config(self) -> RuntimeConfig:
        return self._component_aml_runtime_config("examples-minimal")

    def _component_aml_runtime_config(self, name: str) -> RuntimeConfig:
        # think of this as a worker node running our executables
        reg = os.environ.get("DEVTOOLS_K8S_IMAGE_REGISTRY", "default.local")
        project_tools = self._app.get(projects.PluginServices.PROJECT_TOOLS)
        context_hash = project_tools.image_context_hash()

        # for now :(
        cmds = {
            "rats-devtools": "rats-devtools aml-runtime worker-node",
            "rats-examples-minimal": "python -m rats.minis",
            "rats-examples-datasets": ".venv/bin/python -m rats.exampledatasets",
        }

        # a lot more of this needs to be configurable
        return RuntimeConfig(
            command=cmds[name],
            compute=os.environ.get("DEVTOOLS_AMLRUNTIME_COMPUTE", "default"),
            workspace=AmlWorkspace(
                subscription_id=os.environ.get("DEVTOOLS_AMLRUNTIME_SUBSCRIPTION_ID", ""),
                resource_group_name=os.environ.get("DEVTOOLS_AMLRUNTIME_RESOURCE_GROUP", ""),
                workspace_name=os.environ.get("DEVTOOLS_AMLRUNTIME_WORKSPACE", "default"),
            ),
            environment=AmlEnvironment(
                name=name,
                image=f"{reg}/{name}:{context_hash}",
                version=context_hash,
            ),
        )

    @apps.service(PluginServices.AML_CLIENT)
    def _aml_client(self) -> MLClient:
        workspace = self._app.get(PluginServices.CONFIGS.AML_RUNTIME).workspace
        return MLClient(
            credential=cast(TokenCredential, DefaultAzureCredential()),
            subscription_id=workspace.subscription_id,
            resource_group_name=workspace.resource_group_name,
            workspace_name=workspace.workspace_name,
        )
