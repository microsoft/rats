"""
Provides a way to define a tree of commands, used to generate a command-line interface using Click.

The `CommandTree` class is used to define the tree of commands. Each leaf in the tree represents a
command that can be executed. The nodes can have children, which represent subcommands that can be
executed under the parent command.

The `CommandServiceTree` class is used to define the tree of command using ServiceIds. The tree's
subcommands and handlers are resolved from the container, allowing lazy loading.
"""

from ._click import (
    ClickConversion,
    CommandTreeClickExecutable,
    dataclass_to_click_parameters,
    to_click_commands,
)
from ._command_service_tree import CommandServiceTree
from ._command_tree import CommandTree
from ._docstring import get_attribute_docstring
from ._ids import CommandTreeServices

__all__ = [
    "ClickConversion",
    "CommandServiceTree",
    "CommandTree",
    "CommandTreeClickExecutable",
    "CommandTreeServices",
    "dataclass_to_click_parameters",
    "get_attribute_docstring",
    "to_click_commands",
]
