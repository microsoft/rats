from __future__ import annotations

from collections.abc import Callable
from typing import Any, NamedTuple, TypeVar

from rats import annotations as anns
from rats import apps


class CommandId(NamedTuple):
    """
    A small wrapper around the string name of a [click.Command][].

    Used when wanting to specify a custom name for a command within a [rats.cli.Container][] class.
    See [rats.cli.command][] for more details.
    """

    name: str


AUTO_COMMAND = CommandId("__auto__")
"""
Causes command names to be generated from the method names in [rats.cli.Container][]'s.

This is the default option for [rats.cli.command][] and [rats.cli.group][] and typically does not
need to be used directly.
"""
T = TypeVar("T", bound=Callable[..., Any])


def command(command_id: CommandId = AUTO_COMMAND) -> Callable[[T], T]:
    """
    Mark a method in [rats.cli.Container][] instances as a [click.Command][].

    By default, the name of the method is used to generate a dash-separated command name. You can
    provide a [rats.cli.CommandId][] argument to specify a custom name, for example, if the desired
    command contains characters that are invalid in method names, like periods.

    ```python
    from rats import cli

    class Example(cli.Container):
        @cli.command(cli.CommandId("some.example-command")
        def _any_method_name(self) -> None:
            print("this cli command is called some.example-command")
    ```

    Args:
        command_id: An optional [rats.cli.CommandId][] to specify the command name.
    """

    def decorator(fn: T) -> T:
        if command_id == AUTO_COMMAND:
            cmd_name = fn.__name__.replace("_", "-").strip("-")
            return anns.annotation("commands", CommandId(cmd_name))(fn)
        return anns.annotation("commands", command_id)(fn)

    return decorator


def group(command_id: CommandId = AUTO_COMMAND) -> Callable[..., apps.Executable]:
    """
    Mark a method in [rats.cli.Container][] instances as a [click.Group][].

    !!! warning
        It's unclear if this API is useful as-is and will most likely change soon.

    See [rats.cli.command][] for more details.

    Args:
        command_id: An optional [rats.cli.CommandId][] to specify the group name.
    """

    def decorator(fn: T) -> T:
        if command_id == AUTO_COMMAND:
            return anns.annotation("command-groups", CommandId(fn.__name__.replace("_", "-")))(fn)
        return anns.annotation("command-groups", command_id)(fn)

    return decorator  # type: ignore[reportReturnType]


def get_class_commands(cls: type) -> anns.AnnotationsContainer:
    """Extracts class methods decorated with [rats.cli.command][]."""
    return anns.get_class_annotations(cls).with_namespace("commands")


def get_class_groups(cls: type) -> anns.AnnotationsContainer:
    """Extracts class methods decorated with [rats.cli.group][]."""
    return anns.get_class_annotations(cls).with_namespace("command-groups")
