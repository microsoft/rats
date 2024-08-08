import os
from pathlib import Path

from rats import apps

from ._components import UnsetComponentOperations
from ._tools import ComponentNotFoundError, ComponentOperations, ProjectNotFoundError, ProjectTools


@apps.autoscope
class PluginServices:
    ACTIVE_COMPONENT_OPS = apps.ServiceId[ComponentOperations]("active-component-ops")
    DEVTOOLS_COMPONENT_OPS = apps.ServiceId[ComponentOperations]("devtools-component-ops")
    PROJECT_TOOLS = apps.ServiceId[ProjectTools]("project-tools")

    @staticmethod
    def component_ops(name: str) -> apps.ServiceId[ComponentOperations]:
        return apps.ServiceId[ComponentOperations](f"component-ops[{name}]")


class PluginContainer(apps.Container):
    _app: apps.Container

    def __init__(self, app: apps.Container) -> None:
        self._app = app

    @apps.service(PluginServices.ACTIVE_COMPONENT_OPS)
    def _active_component_ops(self) -> ComponentOperations:
        return self._component_ops(Path().resolve().name)

    @apps.service(PluginServices.DEVTOOLS_COMPONENT_OPS)
    def _devtools_component_ops_alias(self) -> ComponentOperations:
        return self._app.get(PluginServices.component_ops("rats-devtools"))

    @apps.service(PluginServices.component_ops("rats-devtools"))
    def _devtools_component_ops(self) -> ComponentOperations:
        return self._component_ops("rats-devtools")

    @apps.service(PluginServices.component_ops("rats-examples-minimal"))
    def _minimal_component_ops(self) -> ComponentOperations:
        return self._component_ops("rats-examples-minimal")

    @apps.service(PluginServices.component_ops("rats-examples-datasets"))
    def _datasets_component_ops(self) -> ComponentOperations:
        return self._component_ops("rats-examples-datasets")

    def _component_ops(self, name: str) -> ComponentOperations:
        ptools = self._app.get(PluginServices.PROJECT_TOOLS)

        try:
            return ptools.get_component(name)
        except ComponentNotFoundError:
            return UnsetComponentOperations(Path())
        except ProjectNotFoundError:
            return UnsetComponentOperations(Path())

    @apps.service(PluginServices.PROJECT_TOOLS)
    def _project_tools(self) -> ProjectTools:
        return ProjectTools(
            path=Path().resolve(),
            image_registry=os.environ.get("DEVTOOLS_K8S_IMAGE_REGISTRY", "default.local"),
        )
