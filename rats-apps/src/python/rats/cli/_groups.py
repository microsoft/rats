from abc import abstractmethod
from collections.abc import Iterator
from typing import Protocol

import click


class ClickGroupPlugin(Protocol):
    @abstractmethod
    def on_group_open(self, group: click.Group) -> None:
        pass


class AttachGroupCommands(ClickGroupPlugin):
    """
    When a group is opened, attach a set of commands to it.
    """
    _commands: Iterator[click.Command]

    def __init__(self, commands: Iterator[click.Command]) -> None:
        self._commands = commands

    def on_group_open(self, group: click.Group) -> None:
        for command in self._commands:
            group.add_command(command)
