"""Uses `rats.annotations` to streamline the creation of CLI commands written with Click."""

from ._annotations import CommandContainer, CommandId, command, group
from ._click import ClickCommandGroup, ClickCommandMapper
from ._executable import ClickExecutable, ClickGroup
from ._plugins import AttachClickCommands, ClickGroupPlugin

__all__ = [
    "CommandId",
    "command",
    "group",
    "CommandContainer",
    "ClickCommandMapper",
    "ClickExecutable",
    "ClickGroupPlugin",
    "ClickCommandGroup",
    "AttachClickCommands",
    "ClickGroup",
]
