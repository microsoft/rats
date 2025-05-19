from typing import final

import click

from rats import apps

from ._container import Container


@final
class ClickApp(apps.Executable):
    """
    A wrapper to configure and run a [click.Group][] as a [rats.apps.Executable][].

    The [rats.cli.Container][] is attached to the provided [click.Group][] when the
    [rats.cli.ClickApp.execute][] is called, allowing some simple forms of lazy-loading to keep
    commands snappy.
    """

    _group: click.Group
    _commands: Container

    def __init__(
        self,
        group: click.Group,
        commands: Container,
    ) -> None:
        """
        Provide the [rats.cli.Container][] instance that makes up the wanted cli commands.

        Args:
            group: group that will be executed by this application.
            commands: container that will be attached before executing the above group.
        """
        self._group = group
        self._commands = commands

    def execute(self) -> None:
        """
        Attach any commands provided by the [rats.cli.Container][] and then execute the group.

        !!! note
            Currently, this method runs [click.Command.main][] without arguments, causing Click
            to pull the command arguments from [sys.argv][]. If you are needing to change this,
            skip using this class and implement the custom logic yourself.
        """
        self._commands.attach(self._group)
        self._group.main()
