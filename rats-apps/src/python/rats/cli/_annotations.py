from __future__ import annotations

from collections.abc import Callable
from functools import partial
from typing import Any, NamedTuple, TypeVar

import click

from rats import annotations

from ._groups import ClickGroupPlugin


class CommandId(NamedTuple):
    name: str

    # does this api make it impossible to reference a given command that was auto generated?
    @staticmethod
    def auto() -> CommandId:
        return CommandId(name=f"{__name__}:auto")


T = TypeVar("T", bound=Callable)


def command(command_id: CommandId) -> annotations.DecoratorType:
    def decorator(fn: T) -> T:
        if command_id == CommandId.auto():
            return annotations.annotation("commands", CommandId(fn.__name__.replace("_", "-")))(fn)
        return annotations.annotation("commands", command_id)(fn)

    return decorator


def group(command_id: CommandId) -> annotations.DecoratorType:
    def decorator(fn: T) -> T:
        if command_id == CommandId.auto():
            return annotations.annotation(
                "command-groups", CommandId(fn.__name__.replace("_", "-"))
            )(fn)
        return annotations.annotation("commands", command_id)(fn)

    return decorator


def get_class_commands(cls: type) -> annotations.AnnotationsContainer:
    return annotations.get_class_annotations(cls).with_namespace("commands")


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

        for tate in get_class_commands(type(self)).annotations:
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
