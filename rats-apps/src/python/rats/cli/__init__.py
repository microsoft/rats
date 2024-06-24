"""Uses `rats.cli` to streamline the creation of CLI commands written with Click."""

from ._annotations import CommandId, command, group
from ._click import ClickCommandGroup, ClickCommandMapper
from ._executable import ClickExecutable
from ._plugin import PluginContainer, PluginServices
from ._plugins import AttachClickCommands, AttachClickGroup, ClickGroupPlugin, CommandContainer

__all__ = [
    "CommandId",
    "PluginContainer",
    "command",
    "group",
    "PluginServices",
    "ClickCommandMapper",
    "ClickExecutable",
    "ClickGroupPlugin",
    "ClickCommandGroup",
    "AttachClickCommands",
    "AttachClickGroup",
    "CommandContainer",
]
