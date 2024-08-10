# """This is the plugin that should only be enabled when locally developing rats."""
#
# import os
# from pathlib import Path
# from typing import cast
#
# from azure.ai.ml import MLClient
# from azure.core.credentials import TokenCredential
# from azure.identity import DefaultAzureCredential
#
# from rats import apps, cli
# from rats import projects as projects
#
# from ._commands import PluginCommands
# from ._plugin import PluginServices
# from ._runtime import AmlEnvironment, AmlRuntime, AmlWorkspace, RuntimeConfig
#
#
# class PluginContainer(apps.Container):
#     _app: apps.Container
#
#     def __init__(self, app: apps.Container) -> None:
#         self._app = app
#
#     @apps.service(PluginServices.COMMANDS)
#     def _commands(self) -> cli.CommandContainer:
#         return PluginCommands(
#             project_tools=self._app.get(projects.PluginServices.PROJECT_TOOLS),
#             # on worker nodes, we always want the simple local runtime, for now.
#             standard_runtime=self._app.get(apps.AppServices.STANDARD_RUNTIME),
#             aml_runtime=self._app.get(PluginServices.AML_RUNTIME),
#         )
#
#     @apps.service(PluginServices.component_runtime("rats-examples-datasets"))
#     def _datasets_runtime(self) -> AmlRuntime:
#         return self._aml_component_runtime("rats-examples-datasets")
#
#     @apps.service(PluginServices.CONFIGS.component_runtime("rats-examples-datasets"))
#     def _datasets_runtime_config(self) -> RuntimeConfig:
#         return self._component_aml_runtime_config("rats-examples-datasets")
#
#     @apps.service(PluginServices.CONFIGS.component_runtime("rats-examples-minimal"))
#     def _minimal_runtime_config(self) -> RuntimeConfig:
#         return self._component_aml_runtime_config("examples-minimal")
#
