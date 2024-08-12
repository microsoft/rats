import logging
from typing import cast

import click

from rats import apps as apps
from rats import cli as cli
from rats import devtools, kuberuntime, projects

from ._commands import PluginCommands

logger = logging.getLogger(__name__)


@apps.autoscope
class PluginServices:
    COMMANDS = apps.ServiceId[cli.CommandContainer]("commands")
    MAIN_EXE = apps.ServiceId[apps.Executable]("main-exe")
    MAIN_CLICK = apps.ServiceId[click.Group]("main-click")


class PluginContainer(apps.Container):
    _app: apps.Container

    def __init__(self, app: apps.Container) -> None:
        self._app = app

    @apps.group(devtools.PluginServices.EVENTS.OPENING)
    def _on_open(self) -> apps.Executable:
        def run() -> None:
            parent = self._app.get(devtools.PluginServices.MAIN_CLICK)
            docs = self._app.get(PluginServices.MAIN_CLICK)
            parent.add_command(cast(click.Command, docs))

        return apps.App(run)

    @apps.service(PluginServices.COMMANDS)
    def _commands(self) -> cli.CommandContainer:
        return PluginCommands(
            project_tools=self._app.get(projects.PluginServices.PROJECT_TOOLS),
            selected_component=self._app.get(projects.PluginServices.CWD_COMPONENT_TOOLS),
            devtools_component=self._app.get(projects.PluginServices.DEVTOOLS_COMPONENT_TOOLS),
            devtools_runtime=self._app.get(
                kuberuntime.PluginServices.component_runtime("rats-devtools")
            ),
        )

    @apps.service(PluginServices.MAIN_EXE)
    def _main_exe(self) -> apps.Executable:
        return apps.App(lambda: self._app.get(PluginServices.MAIN_CLICK)())

    @apps.service(PluginServices.MAIN_CLICK)
    def _main_click(self) -> click.Group:
        command_container = self._app.get(PluginServices.COMMANDS)
        docs = click.Group(
            "docs",
            help="commands to help author docs-as-code",
        )
        command_container.attach(docs)
        return docs
