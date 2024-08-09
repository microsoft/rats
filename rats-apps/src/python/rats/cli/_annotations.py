from __future__ import annotations

from collections.abc import Callable
from typing import Any, NamedTuple, TypeVar

from rats import annotations as anns
from rats import apps


class CommandId(NamedTuple):
    name: str


EMPTY_COMMAND = CommandId("__empty__")
T = TypeVar("T", bound=Callable[[Any], Any])


def command(command_id: CommandId = EMPTY_COMMAND) -> Callable[..., apps.Executable]:
    def decorator(fn: T) -> T:
        if command_id == EMPTY_COMMAND:
            return anns.annotation("commands", CommandId(fn.__name__.replace("_", "-")))(fn)
        return anns.annotation("commands", command_id)(fn)

    return decorator  # type: ignore[reportReturnType]


def group(command_id: CommandId) -> Callable[[T], T]:
    def decorator(fn: T) -> T:
        if command_id == EMPTY_COMMAND:
            return anns.annotation("command-groups", CommandId(fn.__name__.replace("_", "-")))(fn)
        return anns.annotation("commands", command_id)(fn)

    return decorator


def get_class_commands(cls: type) -> anns.AnnotationsContainer:
    return anns.get_class_annotations(cls).with_namespace("commands")


def get_class_groups(cls: type) -> anns.AnnotationsContainer:
    return anns.get_class_annotations(cls).with_namespace("command-groups")
