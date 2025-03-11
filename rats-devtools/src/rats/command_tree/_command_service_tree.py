from collections.abc import Callable
from contextlib import AbstractContextManager
from dataclasses import dataclass

from rats.apps import Container, ServiceId

from ._command_tree import CommandTree


@dataclass(frozen=True)
class CommandServiceTree:
    """The tree of command services that can be executed."""

    name: str
    """The name of the command service."""

    description: str
    """The description of the command service."""

    children: "ServiceId[CommandServiceTree | CommandTree] | None" = None
    """The children of the command service."""

    kwargs_class: type | None = None
    """The class that represents the arguments of the command service. If None, the command service has no arguments. Arguments are available to the handler and children."""  # noqa: E501

    handler: (
        ServiceId[Callable[..., None] | Callable[..., AbstractContextManager[None]]] | None
    ) = None
    """The handler for the command service. If there are children, the ContextManager wraps their execution, otherwise, the Callable is executed before the children are executed."""  # noqa: E501

    def to_command_tree(self, container: Container) -> "CommandTree":
        """
        Convert the CommandServiceTree to a CommandTree.

        Args:
            container: The container to get the services from.

        Returns:
            The CommandTree representation of the CommandServiceTree.
        """
        return CommandTree(
            name=self.name,
            description=self.description,
            children=(
                tuple(
                    child.to_command_tree(container)
                    if isinstance(child, CommandServiceTree)
                    else child
                    for child in container.get_group(self.children)
                )
                if self.children is not None
                else tuple()
            ),
            kwargs_class=self.kwargs_class,
            handler=container.get(self.handler) if self.handler is not None else None,
        )
