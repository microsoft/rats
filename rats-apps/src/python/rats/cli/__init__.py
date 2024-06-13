"""Uses `rats.cli` to streamline the creation of CLI commands written with Click."""

from ._annotations import CommandId, command, group
from ._click import ClickCommandGroup, ClickCommandMapper
from ._executable import ClickExecutable
from ._plugins import AttachClickCommands, AttachClickGroup, ClickGroupPlugin, CommandContainer

__all__ = [
    "CommandId",
    "command",
    "group",
    "ClickCommandMapper",
    "ClickExecutable",
    "ClickGroupPlugin",
    "ClickCommandGroup",
    "AttachClickCommands",
    "AttachClickGroup",
    "CommandContainer",
]
