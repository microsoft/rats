from dataclasses import dataclass
from typing import Annotated

import click

# pyright seems to struggle with this namespace package
# https://github.com/microsoft/pyright/issues/2882
from rats import apps as apps
from rats import cli as cli
from rats import command_tree as command_tree
from rats import devtools as devtools

from ._commands import PycharmCommands


@dataclass(frozen=True)
class AutoformatterArgs:
    """Arguments for the autoformatter command."""

    filename: Annotated[
        str,
        command_tree.ClickConversion(
            argument=True,
            explicit_click_type=click.Path(exists=True, file_okay=True, dir_okay=False),
        ),
    ]
    """The filename to format."""


@apps.autoscope
class PluginGroups:
    PYCHARM_COMMAND_PLUGINS = apps.ServiceId[cli.ClickGroupPlugin]("cli-plugins[pycharm]")


@apps.autoscope
class PluginServices:
    @staticmethod
    def command(name: str) -> apps.ServiceId[click.Command]:
        return apps.ServiceId(f"cli-commands[{name}]")

    GROUPS = PluginGroups


class RatsPycharmPlugin(apps.AnnotatedContainer):
    _app: apps.Container

    def __init__(self, app: apps.Container) -> None:
        self._app = app

    @apps.group(devtools.AppServices.GROUPS.CLI_ROOT_PLUGINS)
    def pycharm_command(self) -> cli.ClickGroupPlugin:
        return cli.ClickGroup(
            group=lambda: click.Group("pycharm"),
            plugins=apps.PluginRunner(
                iter([PycharmCommands()]),
            ),
        )
