import logging
from collections.abc import Iterator

import click

from rats import apps as apps
from rats import cli as cli
from rats import devtools, projects

from ._commands import PluginCommands

logger = logging.getLogger(__name__)


@apps.autoscope
class PluginServices:
    COMMANDS = apps.ServiceId[cli.Container]("commands")
    MAIN_CLICK = apps.ServiceId[click.Group]("main-click")


class PluginContainer(apps.Container, apps.PluginMixin):
    @apps.group(devtools.AppServices.ON_REGISTER)
    def _on_open(self) -> Iterator[apps.Executable]:
        yield apps.App(
            lambda: cli.attach(
                self._app.get(devtools.AppServices.MAIN_CLICK),
                self._app.get(PluginServices.MAIN_CLICK),
            )
        )

    @apps.service(PluginServices.COMMANDS)
    def _commands(self) -> cli.Container:
        return PluginCommands(
            project_tools=lambda: self._app.get(projects.PluginServices.PROJECT_TOOLS),
            selected_component=lambda: self._app.get(projects.PluginServices.CWD_COMPONENT_TOOLS),
            devtools_component=lambda: self._app.get(
                projects.PluginServices.DEVTOOLS_COMPONENT_TOOLS
            ),
        )

    @apps.service(PluginServices.MAIN_CLICK)
    def _main_click(self) -> click.Group:
        return cli.create_group(
            click.Group(
                "docs",
                help="commands to help author docs-as-code",
            ),
            self._app.get(PluginServices.COMMANDS),
        )
