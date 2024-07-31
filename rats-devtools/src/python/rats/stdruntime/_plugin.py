from typing import cast

import click

from rats import apps, cli
from rats import devtools as devtools
from rats import projects as projects

from ._commands import PluginCommands


@apps.autoscope
class _PluginClickServices:
    GROUP = apps.ServiceId[click.Group]("group")


@apps.autoscope
class PluginServices:
    COMMANDS = apps.ServiceId[cli.CommandContainer]("commands")
    CLICK = _PluginClickServices


class PluginContainer(apps.Container):
    _app: apps.Container

    def __init__(self, app: apps.Container) -> None:
        self._app = app

    @apps.group(cli.PluginServices.EVENTS.command_open(cli.PluginServices.ROOT_COMMAND))
    def _runtime_cli(self) -> apps.Executable:
        def run() -> None:
            group = self._app.get(
                cli.PluginServices.click_command(cli.PluginServices.ROOT_COMMAND)
            )
            stdruntime = self._app.get(PluginServices.CLICK.GROUP)
            self._app.get(PluginServices.COMMANDS).on_group_open(stdruntime)
            group.add_command(cast(click.Command, stdruntime))

        return apps.App(run)

    @apps.service(PluginServices.CLICK.GROUP)
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
