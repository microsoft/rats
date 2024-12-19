"""Uses `rats.cli` to streamline the creation of CLI commands written with Click."""

from ._annotations import CommandId, command, get_class_commands, get_class_groups, group
from ._app import ClickApp
from ._container import CompositeContainer, Container
from ._plugin import PluginServices, attach, create_group

__all__ = [
    "ClickApp",
    "CommandId",
    "CompositeContainer",
    "Container",
    "PluginServices",
    "attach",
    "command",
    "create_group",
    "get_class_commands",
    "get_class_groups",
    "group",
]
