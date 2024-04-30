from abc import abstractmethod
from collections.abc import Callable, Iterator
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
    _command_names: frozenset[str]
    _service_mapper: Callable[[str], apps.ServiceId[click.Command]]
    _container: apps.Container

    def __init__(
        self,
        command_names: frozenset[str],
        service_mapper: Callable[[str], apps.ServiceId[click.Command]],
        container: apps.Container,
    ) -> None:
        self._container = container
        self._service_mapper = service_mapper
        self._command_names = command_names

    def list(self) -> frozenset[str]:
        return self._command_names

    def get(self, name: str) -> click.Command:
        if name not in self._command_names:
            raise ValueError(f"Command {name} not found")

        return self._container.get(self._service_mapper(name))


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
