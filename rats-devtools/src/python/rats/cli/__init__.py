"""Uses `rats.annotations` to streamline the creation of CLI commands written with Click."""

from ._annotations import CommandId, command

__all__ = [
    "CommandId",
    "command",
]
