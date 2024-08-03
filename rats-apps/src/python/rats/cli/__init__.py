"""Uses `rats.cli` to streamline the creation of CLI commands written with Click."""

from ._annotations import CommandId, command, get_class_commands, group
from ._click import ClickCommandGroup, ClickCommandMapper
from ._plugin import PluginContainer, PluginServices
from ._plugins import AttachClickCommands, ClickGroupPlugin, CommandContainer

__all__ = [
    "CommandId",
    "PluginContainer",
    "command",
    "get_class_commands",
    "group",
    "PluginServices",
    "ClickCommandMapper",
    "ClickGroupPlugin",
    "ClickCommandGroup",
    "AttachClickCommands",
    "CommandContainer",
]
