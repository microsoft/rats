"""Uses `rats.annotations` to streamline the creation of CLI commands written with Click."""

from ._annotations import CommandContainer, CommandId, command
from ._groups import CommandGroupPlugin, DeferredCommandGroup

__all__ = [
    "CommandId",
    "command",
    "CommandContainer",
    "CommandProvider",
    "CommandGroupPlugin",
    "DeferredCommandGroup",
]

from ._provider import CommandProvider
