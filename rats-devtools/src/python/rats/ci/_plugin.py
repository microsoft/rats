# pyright seems to struggle with this namespace package
# https://github.com/microsoft/pyright/issues/2882
import os

import click

from rats import apps as apps
from rats import cli as cli
from rats import devtools

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
    def _on_open(self) -> apps.Executable:
        def run() -> None:
            group = self._app.get(
                cli.PluginServices.click_command(cli.PluginServices.ROOT_COMMAND)
            )
            ci = self._app.get(PluginServices.CLICK.GROUP)
            self._app.get(PluginServices.COMMANDS).on_group_open(ci)
            group.add_command(ci)

        return apps.App(run)

    @apps.service(PluginServices.COMMANDS)
    def _commands(self) -> cli.CommandContainer:
        return PluginCommands(
            project_tools=self._app.get(devtools.PluginServices.PROJECT_TOOLS),
            selected_component=self._app.get(devtools.PluginServices.ACTIVE_COMPONENT_OPS),
            devtools_component=self._app.get(devtools.PluginServices.DEVTOOLS_COMPONENT_OPS),
            container_registry=os.environ.get(
                "DEVTOOLS_CONTAINER_REGISTRY", "rats-devtools.default"
            ),
        )

    @apps.service(PluginServices.CLICK.GROUP)
    def _click_group(self) -> click.Group:
        return click.Group(
            "ci",
            help="commands used during ci/cd",
        )
