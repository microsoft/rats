import os
from pathlib import Path

from rats import apps

from ._component_tools import ComponentTools, UnsetComponentTools
from ._project_tools import ComponentNotFoundError, ProjectNotFoundError, ProjectTools


@apps.autoscope
class PluginServices:
    CWD_COMPONENT_TOOLS = apps.ServiceId[ComponentTools]("cwd-component-tools")
    DEVTOOLS_COMPONENT_TOOLS = apps.ServiceId[ComponentTools]("devtools-component-tools")
    PROJECT_TOOLS = apps.ServiceId[ProjectTools]("project-tools")

    @staticmethod
    def component_tools(name: str) -> apps.ServiceId[ComponentTools]:
        return apps.ServiceId[ComponentTools](f"component-tools[{name}]")


class PluginContainer(apps.Container):
    _app: apps.Container

    def __init__(self, app: apps.Container) -> None:
        self._app = app

    @apps.service(PluginServices.CWD_COMPONENT_TOOLS)
    def _active_component_ops(self) -> ComponentTools:
        return self._component_ops(Path().resolve().name)

    @apps.service(PluginServices.DEVTOOLS_COMPONENT_TOOLS)
    def _devtools_component_tools(self) -> ComponentTools:
        project = self._app.get(PluginServices.PROJECT_TOOLS)
        return project.devtools_component()

    def _component_ops(self, name: str) -> ComponentTools:
        ptools = self._app.get(PluginServices.PROJECT_TOOLS)

        try:
            return ptools.get_component(name)
        except ComponentNotFoundError:
            return UnsetComponentTools(Path())
        except ProjectNotFoundError:
            return UnsetComponentTools(Path())

    @apps.service(PluginServices.PROJECT_TOOLS)
    def _project_tools(self) -> ProjectTools:
        return ProjectTools(
            path=Path().resolve(),
            image_registry=os.environ.get("DEVTOOLS_K8S_IMAGE_REGISTRY", "default.local"),
        )
