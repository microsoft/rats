from abc import abstractmethod
from collections.abc import Callable, Iterator, Mapping
from typing import Protocol

import click

from rats import apps

from ._plugins import PluginRunner


class CommandGroupPlugin(Protocol):
    @abstractmethod
    def on_group_registration(self, group: click.Group) -> None:
        pass


class CommandGroup(apps.Executable):
    _plugins: PluginRunner[CommandGroupPlugin]

    def __init__(self, plugins: PluginRunner[CommandGroupPlugin]) -> None:
        self._plugins = plugins

    def execute(self) -> None:
        cli = click.Group()
        self._plugins.apply(lambda plugin: plugin.on_group_registration(cli))
        cli()


class CommandProvider:
    _commands: Mapping[str, Callable[[], click.Command]]

    def __init__(
        self,
        commands: Mapping[str, Callable[[], click.Command]],
    ) -> None:
        self._commands = commands

    def list(self) -> frozenset[str]:
        return frozenset(self._commands.keys())

    def get(self, name: str) -> click.Command:
        if name not in self._commands:
            raise ValueError(f"Command {name} not found")

        return self._commands[name]()


class LazyClickGroup(click.Group):
    _provider: CommandProvider

    def __init__(self, name: str, provider: CommandProvider) -> None:
        super().__init__(name=name)
        self._provider = provider

    def get_command(self, ctx: click.Context, cmd_name: str) -> click.Command | None:
        return self._provider.get(cmd_name)

    def list_commands(self, ctx: click.Context) -> list[str]:
        return list(self._provider.list())


class GroupCommands(CommandGroupPlugin):
    _commands: Iterator[click.Command]

    def __init__(self, commands: Iterator[click.Command]) -> None:
        self._commands = commands

    def on_group_registration(self, group: click.Group) -> None:
        for command in self._commands:
            group.add_command(command)
