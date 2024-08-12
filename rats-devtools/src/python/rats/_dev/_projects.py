from rats import apps
from rats import projects as projects


class ProjectPluginContainer(apps.Container):
    _app: apps.Container

    def __init__(self, app: apps.Container) -> None:
        self._app = app

    @apps.service(projects.PluginServices.component_tools("rats-devtools"))
    def _devtools_component_tools(self) -> projects.ComponentTools:
        return self._app.get(projects.PluginServices.PROJECT_TOOLS).get_component("rats-devtools")

    @apps.service(projects.PluginServices.component_tools("rats-examples-minimal"))
    def _minimal_component_tools(self) -> projects.ComponentTools:
        return self._app.get(projects.PluginServices.PROJECT_TOOLS).get_component(
            "rats-examples-minimal",
        )

    @apps.service(projects.PluginServices.component_tools("rats-examples-datasets"))
    def _datasets_component_tools(self) -> projects.ComponentTools:
        return self._app.get(projects.PluginServices.PROJECT_TOOLS).get_component(
            "rats-examples-datasets",
        )
