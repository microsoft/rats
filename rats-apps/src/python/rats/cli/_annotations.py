from __future__ import annotations

from collections.abc import Callable
from typing import Any, NamedTuple, TypeVar

from rats import annotations as anns


class CommandId(NamedTuple):
    name: str

    # does this api make it impossible to reference a given command that was auto generated?
    @staticmethod
    def auto() -> CommandId:
        return CommandId(name=f"{__name__}:auto")


T = TypeVar("T", bound=Callable[[Any], Any])


def command(command_id: CommandId) -> Callable[[T], T]:
    def decorator(fn: T) -> T:
        if command_id == CommandId.auto():
            return anns.annotation("commands", CommandId(fn.__name__.replace("_", "-")))(fn)
        return anns.annotation("commands", command_id)(fn)

    return decorator


def group(command_id: CommandId) -> Callable[[T], T]:
    def decorator(fn: T) -> T:
        if command_id == CommandId.auto():
            return anns.annotation("command-groups", CommandId(fn.__name__.replace("_", "-")))(fn)
        return anns.annotation("commands", command_id)(fn)

    return decorator


def get_class_commands(cls: type) -> anns.AnnotationsContainer:
    return anns.get_class_annotations(cls).with_namespace("commands")
