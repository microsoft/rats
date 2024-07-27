import os
from typing import cast

from azure.ai.ml import MLClient
from azure.ai.ml.operations import EnvironmentOperations, JobOperations
from azure.core.credentials import TokenCredential
from azure.identity import DefaultAzureCredential

from rats import apps, devtools

from ._runtime import AmlEnvironment, AmlRuntime, AmlWorkspace, RuntimeConfig


@apps.autoscope
class _PluginConfigs:
    AML_RUNTIME = apps.ConfigId[RuntimeConfig]("aml-runtime")


@apps.autoscope
class PluginServices:
    AML_RUNTIME = apps.ServiceId[AmlRuntime]("aml-runtime")
    AML_CLIENT = apps.ServiceId[MLClient]("aml-client")
    AML_ENVIRONMENT_OPERATIONS = apps.ServiceId[EnvironmentOperations](
        "aml-environment-operations"
    )
    AML_JOB_OPERATIONS = apps.ServiceId[JobOperations]("aml-job-operations")
    HELLO_WORLD = apps.ServiceId[apps.Executable]("hello-world")

    CONFIGS = _PluginConfigs


class PluginContainer(apps.Container):
    _app: apps.Container

    def __init__(self, app: apps.Container) -> None:
        self._app = app

    @apps.service(PluginServices.HELLO_WORLD)
    def _hello_world(self) -> apps.Executable:
        return apps.App(lambda: print("hello, world!"))

    @apps.service(PluginServices.AML_RUNTIME)
    def _aml_runtime(self) -> AmlRuntime:
        return AmlRuntime(
            ml_client=self._app.get(PluginServices.AML_CLIENT),
            environment_operations=self._app.get(PluginServices.AML_ENVIRONMENT_OPERATIONS),
            job_operations=self._app.get(PluginServices.AML_JOB_OPERATIONS),
            config=lambda: self._app.get(PluginServices.CONFIGS.AML_RUNTIME),
        )

    @apps.service(PluginServices.AML_ENVIRONMENT_OPERATIONS)
    def _aml_env_ops(self) -> EnvironmentOperations:
        return self._app.get(PluginServices.AML_CLIENT).environments

    @apps.service(PluginServices.AML_JOB_OPERATIONS)
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
        reg = os.environ.get("DEVTOOLS_K8S_IMAGE_REGISTRY", "default.local")
        project_tools = self._app.get(devtools.PluginServices.PROJECT_TOOLS)
        active_component = self._app.get(devtools.PluginServices.ACTIVE_COMPONENT_OPS)
        name = active_component.find_path(".").name
        context_hash = project_tools.image_context_hash()

        image = f"{reg}/{name}:{context_hash}"

        return RuntimeConfig(
            command=os.environ.get("DEVTOOLS_AMLRUNTIME_COMMAND", "echo hello, world!"),
            compute=os.environ.get("DEVTOOLS_AMLRUNTIME_COMPUTE", "default"),
            workspace=AmlWorkspace(
                subscription_id=os.environ.get("DEVTOOLS_AMLRUNTIME_SUBSCRIPTION_ID"),
                resource_group_name=os.environ.get("DEVTOOLS_AMLRUNTIME_RESOURCE_GROUP"),
                workspace_name=os.environ.get("DEVTOOLS_AMLRUNTIME_WORKSPACE"),
            ),
            environment=AmlEnvironment(
                name=name,
                image=image,
                version=context_hash,
            ),
        )
