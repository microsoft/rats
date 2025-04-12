"""Use `rats.cli` to streamline the creation of CLI commands written with Click."""

from ._annotations import (
    AUTO_COMMAND,
    CommandId,
    command,
    get_class_commands,
    get_class_groups,
    group,
)
from ._click_app import ClickApp
from ._command import Command
from ._container import CompositeContainer, Container
from ._functions import attach, create_group
from ._plugin import PluginConfigs, PluginContainer

__all__ = [
    "AUTO_COMMAND",
    "ClickApp",
    "Command",
    "CommandId",
    "CompositeContainer",
    "Container",
    "PluginConfigs",
    "PluginContainer",
    "attach",
    "command",
    "create_group",
    "get_class_commands",
    "get_class_groups",
    "group",
]
