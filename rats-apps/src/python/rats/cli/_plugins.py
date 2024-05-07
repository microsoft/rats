from __future__ import annotations

from abc import abstractmethod
from collections.abc import Callable, Iterator
from functools import partial
from typing import Any, Protocol

import click

from rats import apps

from ._annotations import get_class_commands


class ClickGroupPlugin(Protocol):
    @abstractmethod
    def on_group_open(self, group: click.Group) -> None:
        pass


class AttachClickCommands(ClickGroupPlugin):
    """When a group is opened, attach a set of commands to it."""

    _commands: Iterator[click.Command]

    def __init__(self, commands: Iterator[click.Command]) -> None:
        self._commands = commands

    def on_group_open(self, group: click.Group) -> None:
        for command in self._commands:
            group.add_command(command)


class AttachClickGroup(ClickGroupPlugin):
    _group: apps.ServiceProvider[click.Group]
    _plugins: apps.PluginRunner[ClickGroupPlugin]

    def __init__(
        self,
        group: apps.ServiceProvider[click.Group],
        plugins: apps.PluginRunner[ClickGroupPlugin],
    ) -> None:
        self._group = group
        self._plugins = plugins

    def on_group_open(self, group: click.Group) -> None:
        cmd = self._group()
        self._plugins.apply(lambda plugin: plugin.on_group_open(cmd))
        group.add_command(cmd)


class CommandContainer(ClickGroupPlugin):
    def on_group_open(self, group: click.Group) -> None:
        def cb(_method: Callable[[Any], Any], *args: Any, **kwargs: Any) -> None:
            """
            Callback handed to `click.Command`. Calls the method with matching name on this class.

            When the command is decorated with `@click.params` and `@click.option`, `click` will
            call this callback with the parameters in the order they were defined. This callback
            then calls the method with the same name on this class, passing the parameters in
            reverse order. This is because the method is defined with the parameters in the
            reverse order to the decorator, so we need to reverse them again to get the correct
            order.
            """
            _method(*args, **kwargs)

        commands = get_class_commands(type(self))
        tates = commands.annotations

        for tate in tates:
            method = getattr(self, tate.name)
            params = list(reversed(getattr(method, "__click_params__", [])))
            for command in tate.groups:
                group.add_command(
                    click.Command(
                        name=command.name,
                        callback=partial(cb, method),
                        short_help=method.__doc__,
                        params=params,
                    )
                )
