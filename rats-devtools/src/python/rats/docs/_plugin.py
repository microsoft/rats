# pyright seems to struggle with this namespace package
# https://github.com/microsoft/pyright/issues/2882
from typing import cast

import click

from rats import apps as apps
from rats import cli as cli
from rats import kuberuntime, projects

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
            docs = self._app.get(PluginServices.CLICK.GROUP)
            self._app.get(PluginServices.COMMANDS).attach(docs)
            group.add_command(cast(click.Command, docs))

        return apps.App(run)

    @apps.service(PluginServices.COMMANDS)
    def _commands(self) -> cli.CommandContainer:
        return PluginCommands(
            project_tools=self._app.get(projects.PluginServices.PROJECT_TOOLS),
            selected_component=self._app.get(projects.PluginServices.ACTIVE_COMPONENT_OPS),
            devtools_component=self._app.get(projects.PluginServices.DEVTOOLS_COMPONENT_OPS),
            devtools_runtime=self._app.get(
                kuberuntime.PluginServices.component_runtime("rats-devtools")
            ),
        )

    @apps.service(PluginServices.CLICK.GROUP)
    def _click_group(self) -> click.Group:
        return click.Group(
            "docs",
            help="commands to help author docs-as-code",
        )
