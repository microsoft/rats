"""Uses `rats.cli` to streamline the creation of CLI commands written with Click."""

from ._annotations import CommandId, command, get_class_commands, get_class_groups, group
from ._app import ClickApp
from ._container import Container
from ._plugin import PluginContainer, PluginServices, attach, create_group

__all__ = [
    "PluginContainer",
    "command",
    "get_class_commands",
    "get_class_groups",
    "create_group",
    "attach",
    "group",
    "ClickApp",
    "PluginServices",
    "CommandId",
    "Container",
]
