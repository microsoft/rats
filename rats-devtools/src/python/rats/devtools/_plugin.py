# pyright seems to struggle with this namespace package
# https://github.com/microsoft/pyright/issues/2882
import logging
from pathlib import Path

from rats import apps as apps
from rats import cli, logs

from ._component_operations import ComponentOperations, UnsetComponentOperations
from ._project_tools import ComponentNotFoundError, ProjectTools

logger = logging.getLogger(__name__)


@apps.autoscope
class _PluginEvents:
    APP_OPEN = apps.ServiceId[apps.Executable]("app-open")
    APP_RUN = apps.ServiceId[apps.Executable]("app-run")
    APP_CLOSE = apps.ServiceId[apps.Executable]("app-close")


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
                PluginServices.EVENTS.APP_OPEN,
                PluginServices.EVENTS.APP_RUN,
                PluginServices.EVENTS.APP_CLOSE,
            )
        )

    @apps.group(PluginServices.EVENTS.APP_OPEN)
    def _on_app_open(self) -> apps.Executable:
        return apps.App(lambda: logger.debug("Opening app"))

    @apps.group(PluginServices.EVENTS.APP_RUN)
    def _on_app_run(self) -> apps.Executable:
        return self._app.get(cli.PluginServices.ROOT_COMMAND)

    @apps.group(PluginServices.EVENTS.APP_CLOSE)
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
