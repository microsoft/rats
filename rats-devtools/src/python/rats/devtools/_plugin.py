import logging
from collections.abc import Iterator

import click

from rats import apps, cli, logs
from rats import projects as projects

from ._commands import PluginCommands

logger = logging.getLogger(__name__)


@apps.autoscope
class _PluginEvents:
    OPENING = apps.ServiceId[apps.Executable]("opening")
    RUNNING = apps.ServiceId[apps.Executable]("running")
    CLOSING = apps.ServiceId[apps.Executable]("closing")


@apps.autoscope
class PluginServices:
    MAIN_EXE = apps.ServiceId[apps.Executable]("main-exe")
    MAIN_CLICK = apps.ServiceId[click.Group]("main-click")
    COMMANDS = apps.ServiceId[cli.CommandContainer]("commands")
    EVENTS = _PluginEvents


class PluginContainer(apps.Container):
    _app: apps.Container

    def __init__(self, app: apps.Container) -> None:
        self._app = app

    @apps.group(PluginServices.EVENTS.OPENING)
    def _on_opening(self) -> Iterator[apps.Executable]:
        runtime = self._app.get(apps.AppServices.RUNTIME)
        yield apps.App(
            lambda: runtime.execute_group(logs.PluginServices.EVENTS.CONFIGURE_LOGGING),
        )

    @apps.group(PluginServices.EVENTS.RUNNING)
    def _on_running(self) -> Iterator[apps.Executable]:
        # our main app here runs a cli command, but it can also directly do something useful
        runtime = self._app.get(apps.AppServices.RUNTIME)
        yield apps.App(lambda: runtime.execute(PluginServices.MAIN_EXE))

    @apps.group(PluginServices.EVENTS.CLOSING)
    def _on_closing(self) -> Iterator[apps.Executable]:
        yield apps.App(lambda: logger.debug("Closing app"))

    @apps.service(PluginServices.MAIN_EXE)
    def _main_exe(self) -> apps.Executable:
        return apps.App(lambda: self._app.get(PluginServices.MAIN_CLICK)())

    @apps.service(PluginServices.MAIN_CLICK)
    def _main_click(self) -> click.Group:
        root = click.Group(
            "rats-devtools",
            help="develop your ideas with ease",
        )
        return root

    @apps.group(PluginServices.EVENTS.OPENING)
    def _on_open(self) -> Iterator[apps.Executable]:
        def run() -> None:
            parent = self._app.get(PluginServices.MAIN_CLICK)
            self._app.get(PluginServices.COMMANDS).attach(parent)

        yield apps.App(run)

    @apps.service(PluginServices.COMMANDS)
    def _commands(self) -> cli.CommandContainer:
        return PluginCommands(lambda: self._app.get(projects.PluginServices.PROJECT_TOOLS))
