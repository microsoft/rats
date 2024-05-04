"""Uses `rats.annotations` to streamline the creation of CLI commands written with Click."""

from ._annotations import CommandContainer, CommandId, command, group
from ._executable import ClickExecutable, ClickGroup
from ._groups import ClickGroupPlugin, DeferredCommandGroup, GroupCommands

__all__ = [
    "CommandId",
    "command",
    "group",
    "CommandContainer",
    "CommandProvider",
    "ClickExecutable",
    "ClickGroupPlugin",
    "DeferredCommandGroup",
    "GroupCommands",
    "ClickGroup",
]

from ._provider import CommandProvider
