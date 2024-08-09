from typing import final

import click

from rats import apps

from ._container import CommandContainer


@final
class ClickApp(apps.Executable):
    """..."""

    _group: click.Group
    _commands: CommandContainer

    def __init__(
        self,
        group: click.Group,
        commands: CommandContainer,
    ) -> None:
        """Not sure this is the right interface."""
        self._group = group
        self._commands = commands

    def execute(self) -> None:
        """This app executes a click application after letting rats plugins attach commands."""
        self._commands.attach(self._group)
        self._group.main()