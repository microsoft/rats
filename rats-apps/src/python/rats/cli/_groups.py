from abc import abstractmethod
from typing import Iterator, Protocol, final

import click

from ._provider import CommandProvider


@final
class DeferredCommandGroup(click.Group):
    _provider: CommandProvider

    def __init__(self, name: str, provider: CommandProvider) -> None:
        super().__init__(name=name)
        self._provider = provider

    def get_command(self, ctx: click.Context, cmd_name: str) -> click.Command | None:
        return self._provider.get(cmd_name)

    def list_commands(self, ctx: click.Context) -> list[str]:
        return list(self._provider.list())


class ClickGroupPlugin(Protocol):
    @abstractmethod
    def on_group_open(self, group: click.Group) -> None:
        pass


class GroupCommands(ClickGroupPlugin):
    _commands: Iterator[click.Command]

    def __init__(self, commands: Iterator[click.Command]) -> None:
        self._commands = commands

    def on_group_open(self, group: click.Group) -> None:
        for command in self._commands:
            group.add_command(command)
