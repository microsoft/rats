import os

from rats import amlruntime, projects
from rats import apps as apps


class AmlRuntimePluginContainer(apps.Container):
    _app: apps.Container

    def __init__(self, app: apps.Container) -> None:
        self._app = app

    @apps.service(amlruntime.PluginServices.component_runtime("rats-devtools"))
    def _devtools_runtime(self) -> amlruntime.AmlRuntime:
        return self._make_runtime("rats-devtools")

    @apps.service(amlruntime.PluginServices.component_runtime("rats-examples-minimal"))
    def _minimal_runtime(self) -> amlruntime.AmlRuntime:
        return self._make_runtime("rats-examples-minimal")

    @apps.service(amlruntime.PluginServices.component_runtime("rats-examples-datasets"))
    def _datasets_runtime(self) -> amlruntime.AmlRuntime:
        return self._make_runtime("rats-examples-datasets")

    def _make_runtime(self, name: str) -> amlruntime.AmlRuntime:
        return amlruntime.AmlRuntime(
            ml_client=lambda: self._app.get(amlruntime.PluginServices.AML_CLIENT),
            environment_operations=lambda: self._app.get(
                amlruntime.PluginServices.AML_ENVIRONMENT_OPS,
            ),
            job_operations=lambda: self._app.get(amlruntime.PluginServices.AML_JOB_OPS),
            config=lambda: self._app.get(
                amlruntime.PluginServices.CONFIGS.component_runtime(name)
            ),
        )

    @apps.service(amlruntime.PluginServices.CONFIGS.component_runtime("rats-examples-datasets"))
    def _datasets_runtime_config(self) -> amlruntime.RuntimeConfig:
        return self._component_aml_runtime_config("rats-examples-datasets")

    @apps.service(amlruntime.PluginServices.CONFIGS.component_runtime("rats-examples-minimal"))
    def _minimal_runtime_config(self) -> amlruntime.RuntimeConfig:
        return self._component_aml_runtime_config("rats-examples-minimal")

    @apps.service(amlruntime.PluginServices.CONFIGS.component_runtime("rats-devtools"))
    def _devtools_runtime_config(self) -> amlruntime.RuntimeConfig:
        return self._component_aml_runtime_config("rats-devtools")

    def _component_aml_runtime_config(self, name: str) -> amlruntime.RuntimeConfig:
        # think of this as a worker node running our executables
        reg = os.environ.get("DEVTOOLS_K8S_IMAGE_REGISTRY", "default.local")
        project_tools = self._app.get(projects.PluginServices.PROJECT_TOOLS)
        context_hash = project_tools.image_context_hash()

        # for now :(
        cmds = {
            "rats-devtools": " && ".join(
                [
                    "cd /opt/rats/rats-devtools",
                    "bin/rats-devtools aml-runtime worker-node",
                ]
            ),
            "rats-examples-minimal": " && ".join(
                [
                    "cd /opt/rats/rats-examples-minimal",
                    ".venv/bin/python -m rats.examples",
                ]
            ),
            "rats-examples-datasets": " && ".join(
                [
                    "cd /opt/rats/rats-examples-datasets",
                    ".venv/bin/python -m rats.examples",
                ]
            ),
        }

        # a lot more of this needs to be configurable
        return amlruntime.RuntimeConfig(
            command=cmds[name],
            env_variables=dict(),
            compute=os.environ.get("DEVTOOLS_AMLRUNTIME_COMPUTE", "default"),
            workspace=amlruntime.AmlWorkspace(
                subscription_id=os.environ.get("DEVTOOLS_AMLRUNTIME_SUBSCRIPTION_ID", ""),
                resource_group_name=os.environ.get("DEVTOOLS_AMLRUNTIME_RESOURCE_GROUP", ""),
                workspace_name=os.environ.get("DEVTOOLS_AMLRUNTIME_WORKSPACE", "default"),
            ),
            environment=amlruntime.AmlEnvironment(
                name=name,
                image=f"{reg}/{name}:{context_hash}",
                version=context_hash,
            ),
        )
