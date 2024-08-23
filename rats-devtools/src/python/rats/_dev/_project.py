from rats import apps
from rats import projects as projects


class ProjectPluginContainer(apps.Container):
    _app: apps.Container

    def __init__(self, app: apps.Container) -> None:
        self._app = app

    @apps.container()
    def _project_structure(self) -> apps.Container:
        return apps.StaticContainer(
            apps.StaticProvider(
                apps.ProviderNamespaces.SERVICES,
                projects.PluginServices.component_tools("rats-devtools"),
                lambda: self._app.get(
                    projects.PluginServices.PROJECT_TOOLS,
                ).get_component("rats-devtools"),
            ),
            apps.StaticProvider(
                apps.ProviderNamespaces.SERVICES,
                projects.PluginServices.component_tools("rats-examples-datasets"),
                lambda: self._app.get(
                    projects.PluginServices.PROJECT_TOOLS,
                ).get_component("rats-examples-datasets"),
            ),
            apps.StaticProvider(
                apps.ProviderNamespaces.SERVICES,
                projects.PluginServices.component_tools("rats-contrib-jesus"),
                lambda: self._app.get(
                    projects.PluginServices.PROJECT_TOOLS,
                ).get_component("rats-contrib-jesus"),
            ),
        )
