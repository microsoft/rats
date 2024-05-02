from collections.abc import Iterator

import click

# pyright seems to struggle with this namespace package
# https://github.com/microsoft/pyright/issues/2882
from rats import apps as apps
from rats import cli as cli

from ._plugins import PluginRunner


class CommandGroup(apps.Executable):
    _plugins: PluginRunner[cli.CommandGroupPlugin]

    def __init__(self, plugins: PluginRunner[cli.CommandGroupPlugin]) -> None:
        self._plugins = plugins

    def execute(self) -> None:
        cli = click.Group()
        self._plugins.apply(lambda plugin: plugin.on_group_open(cli))
        cli()


class GroupCommands(cli.CommandGroupPlugin):
    _commands: Iterator[click.Command]

    def __init__(self, commands: Iterator[click.Command]) -> None:
        self._commands = commands

    def on_group_open(self, group: click.Group) -> None:
        for command in self._commands:
            group.add_command(command)
