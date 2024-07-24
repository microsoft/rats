import os
from pathlib import Path

from rats import apps, devtools, projects

from ._runtime import K8sRuntime, K8sRuntimeConfig, K8sWorkflowRun, KustomizeImage


@apps.autoscope
class PluginServices:
    K8S_RUNTIME = apps.ServiceId[K8sRuntime]("k8s-runtime")

    @staticmethod
    def component_runtime(name: str) -> apps.ServiceId[K8sRuntime]:
        return apps.ServiceId[K8sRuntime](f"{PluginServices.K8S_RUNTIME}[{name}]")


class PluginContainer(apps.Container):
    _app: apps.Container

    def __init__(self, app: apps.Container) -> None:
        self._app = app

    @apps.service(PluginServices.K8S_RUNTIME)
    def _k8s_runtime(self) -> apps.Runtime:
        try:
            return self._app.get(PluginServices.component_runtime(Path().resolve().name))
        except apps.ServiceNotFoundError as e:
            if e.service_id == PluginServices.component_runtime(Path().resolve().name):
                return apps.NullRuntime()
            raise

    @apps.service(PluginServices.component_runtime("rats-devtools"))
    def _devtools_runtime(self) -> K8sRuntime:
        return self._k8s_component_runtime("rats-devtools")

    @apps.service(PluginServices.component_runtime("rats-examples-minimal"))
    def _minimal_runtime(self) -> K8sRuntime:
        return self._k8s_component_runtime("rats-examples-minimal")

    def _k8s_component_runtime(self, name: str) -> K8sRuntime:
        def _container_images() -> tuple[KustomizeImage, ...]:
            reg = os.environ.get("DEVTOOLS_K8S_IMAGE_REGISTRY", "default.local")
            project_tools = self._app.get(devtools.PluginServices.PROJECT_TOOLS)
            context_hash = project_tools.image_context_hash()
            return (
                KustomizeImage(
                    "rats-devtools",
                    f"{reg}/rats-devtools",
                    context_hash,
                ),
                KustomizeImage(
                    "rats-examples-minimal",
                    f"{reg}/rats-examples-minimal",
                    context_hash,
                ),
            )

        def _factory(
            id: str,
            exe_ids: tuple[apps.ServiceId[apps.T_ExecutableType], ...],
            group_ids: tuple[apps.ServiceId[apps.T_ExecutableType], ...],
        ) -> K8sWorkflowRun:
            return K8sWorkflowRun(
                devops_component=self._app.get(devtools.PluginServices.DEVTOOLS_COMPONENT_OPS),
                main_component=self._app.get(devtools.PluginServices.component_ops(name)),
                main_component_id=projects.ComponentId(name),
                k8s_config_context=os.environ.get("DEVTOOLS_K8S_CONFIG_CONTEXT", "default"),
                container_images=_container_images(),
                id=id,
                exe_ids=exe_ids,
                group_ids=group_ids,
            )

        return K8sRuntime(
            config=lambda: K8sRuntimeConfig(
                id=os.environ.get("DEVTOOLS_K8S_CONTEXT_ID", "/"),
                container_images=_container_images(),
                main_component=projects.ComponentId(name),
            ),
            factory=_factory,
        )
