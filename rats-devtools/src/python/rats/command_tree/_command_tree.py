from collections.abc import Callable
from contextlib import AbstractContextManager
from dataclasses import dataclass


@dataclass(frozen=True)
class CommandTree:
    """The tree of commands that can be executed."""

    name: str
    """The name of the command."""

    description: str
    """The description of the command."""

    children: tuple["CommandTree", ...] = tuple()
    """The children of the command."""

    kwargs_class: type | None = None
    """The class that represents the arguments of the command. If None, the command has no arguments. Arguments are available to the handler and children."""  # noqa: E501

    handler: Callable[..., None] | Callable[..., AbstractContextManager[None]] | None = None
    """The handler for the command. If there are children, the ContextManager wraps their execution, otherwise, the Callable is executed before the children are executed."""  # noqa: E501
