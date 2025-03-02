import os

from rats import apps as apps
from rats import kuberuntime, projects


class KubeRuntimePluginContainer(apps.Container, apps.PluginMixin):
    @apps.service(kuberuntime.PluginServices.component_runtime("rats-devtools"))
    def _devtools_runtime(self) -> kuberuntime.K8sRuntime:
        return self._k8s_component_runtime("rats-devtools")

    @apps.service(kuberuntime.PluginServices.component_command("rats-devtools"))
    def _devtools_command(self) -> tuple[str, ...]:
        return ("bin/rats-examples",)

    def _k8s_component_runtime(self, name: str) -> kuberuntime.K8sRuntime:
        def _container_images() -> tuple[kuberuntime.KustomizeImage, ...]:
            reg = os.environ.get("DEVTOOLS_IMAGE_REGISTRY", "default.local")
            project_tools = self._app.get(projects.PluginServices.PROJECT_TOOLS)
            context_hash = project_tools.image_context_hash()
            return (
                kuberuntime.KustomizeImage(
                    "rats-devtools",
                    f"{reg}/rats-devtools",
                    context_hash,
                ),
            )

        def _factory(
            id: str,
            exe_ids: tuple[apps.ServiceId[apps.T_ExecutableType], ...],
            group_ids: tuple[apps.ServiceId[apps.T_ExecutableType], ...],
        ) -> kuberuntime.K8sWorkflowRun:
            tools = self._app.get(projects.PluginServices.PROJECT_TOOLS)
            return kuberuntime.K8sWorkflowRun(
                devops_component=self._app.get(projects.PluginServices.DEVTOOLS_COMPONENT_TOOLS),
                main_component=tools.get_component(name),
                main_component_id=projects.ComponentId(name),
                k8s_config_context=os.environ.get("DEVTOOLS_K8S_CONFIG_CONTEXT", "default"),
                container_images=_container_images(),
                command=self._app.get(kuberuntime.PluginServices.component_command(name)),
                id=id,
                exe_ids=exe_ids,  # type: ignore
                group_ids=group_ids,  # type: ignore
            )

        return kuberuntime.K8sRuntime(
            config=lambda: kuberuntime.RuntimeConfig(
                id=os.environ.get("DEVTOOLS_K8S_CONTEXT_ID", "/"),
                command=("rats-examples",),
                container_images=_container_images(),
                main_component=projects.ComponentId(name),
            ),
            factory=_factory,  # type: ignore
        )
