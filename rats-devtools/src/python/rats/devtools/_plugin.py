import logging
from pathlib import Path

from rats import apps, cli, logs

from ._component_operations import ComponentOperations, UnsetComponentOperations
from ._project_tools import ComponentNotFoundError, ProjectTools

logger = logging.getLogger(__name__)


@apps.autoscope
class _PluginEvents:
    @staticmethod
    def app_open(app: apps.ServiceId[apps.Executable]) -> apps.ServiceId[apps.Executable]:
        return apps.ServiceId(f"{app.name}[open]")

    @staticmethod
    def app_run(app: apps.ServiceId[apps.Executable]) -> apps.ServiceId[apps.Executable]:
        return apps.ServiceId(f"{app.name}[run]")

    @staticmethod
    def app_close(app: apps.ServiceId[apps.Executable]) -> apps.ServiceId[apps.Executable]:
        return apps.ServiceId(f"{app.name}[close]")


@apps.autoscope
class PluginServices:
    MAIN = apps.ServiceId[apps.Executable]("main")
    ACTIVE_COMPONENT_OPS = apps.ServiceId[ComponentOperations]("active-component-ops")
    DEVTOOLS_COMPONENT_OPS = apps.ServiceId[ComponentOperations]("devtools-component-ops")
    PROJECT_TOOLS = apps.ServiceId[ProjectTools]("project-tools")
    EVENTS = _PluginEvents


class PluginContainer(apps.Container):
    _app: apps.Container

    def __init__(self, app: apps.Container) -> None:
        self._app = app

    @apps.service(PluginServices.MAIN)
    def _main(self) -> apps.Executable:
        runtime = self._app.get(apps.AppServices.RUNTIME)
        return apps.App(
            lambda: runtime.execute_group(
                logs.PluginServices.EVENTS.CONFIGURE_LOGGING,
                PluginServices.EVENTS.app_open(PluginServices.MAIN),
                PluginServices.EVENTS.app_run(PluginServices.MAIN),
                PluginServices.EVENTS.app_close(PluginServices.MAIN),
            )
        )

    @apps.group(PluginServices.EVENTS.app_open(PluginServices.MAIN))
    def _on_app_open(self) -> apps.Executable:
        return apps.App(lambda: logger.debug("Opening app"))

    @apps.group(PluginServices.EVENTS.app_run(PluginServices.MAIN))
    def _on_app_run(self) -> apps.Executable:
        return self._app.get(cli.PluginServices.ROOT_COMMAND)

    @apps.group(PluginServices.EVENTS.app_run(PluginServices.MAIN))
    def _on_app_close(self) -> apps.Executable:
        return apps.App(lambda: logger.debug("Closing app"))

    @apps.service(PluginServices.ACTIVE_COMPONENT_OPS)
    def _active_component_ops(self) -> ComponentOperations:
        ptools = self._app.get(PluginServices.PROJECT_TOOLS)
        try:
            return ptools.get_component(Path().resolve().name)
        except ComponentNotFoundError:
            return UnsetComponentOperations(Path())

    @apps.service(PluginServices.DEVTOOLS_COMPONENT_OPS)
    def _devtools_component_ops(self) -> ComponentOperations:
        ptools = self._app.get(PluginServices.PROJECT_TOOLS)
        return ptools.get_component("rats-devtools")

    @apps.service(PluginServices.PROJECT_TOOLS)
    def _project_tools(self) -> ProjectTools:
        return ProjectTools(Path().resolve())
