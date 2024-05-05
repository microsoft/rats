from __future__ import annotations

from collections.abc import Callable
from typing import NamedTuple, TypeVar

from rats import annotations


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
