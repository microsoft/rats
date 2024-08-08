from typing import cast

import click

from rats import apps, cli
from rats import devtools as devtools

from ._commands import PluginCommands


@apps.autoscope
class PluginServices:
    COMMANDS = apps.ServiceId[cli.CommandContainer]("commands")
    MAIN_CLICK = apps.ServiceId[click.Group]("main-click")


class PluginContainer(apps.Container):
    _app: apps.Container

    def __init__(self, app: apps.Container) -> None:
        self._app = app

    @apps.group(devtools.PluginServices.EVENTS.OPENING)
    def _runtime_cli(self) -> apps.Executable:
        def run() -> None:
            parent = self._app.get(devtools.PluginServices.MAIN_CLICK)
            stdruntime = self._app.get(PluginServices.MAIN_CLICK)
            self._app.get(PluginServices.COMMANDS).attach(stdruntime)
            parent.add_command(cast(click.Command, stdruntime))

        return apps.App(run)

    @apps.service(PluginServices.MAIN_CLICK)
    def _click_group(self) -> click.Group:
        return click.Group(
            "std-runtime",
            help="submit executables and events to the in-thread runtime.",
        )

    @apps.service(PluginServices.COMMANDS)
    def _commands(self) -> cli.CommandContainer:
        return PluginCommands(
            standard_runtime=self._app.get(apps.AppServices.STANDARD_RUNTIME),
        )
