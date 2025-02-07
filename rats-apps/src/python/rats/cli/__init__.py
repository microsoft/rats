"""Use `rats.cli` to streamline the creation of CLI commands written with Click."""

from ._annotations import (
    AUTO_COMMAND,
    CommandId,
    command,
    get_class_commands,
    get_class_groups,
    group,
)
from ._app import ClickApp
from ._container import CompositeContainer, Container
from ._plugin import attach, create_group

__all__ = [
    "AUTO_COMMAND",
    "ClickApp",
    "CommandId",
    "CompositeContainer",
    "Container",
    "attach",
    "command",
    "create_group",
    "get_class_commands",
    "get_class_groups",
    "group",
]
