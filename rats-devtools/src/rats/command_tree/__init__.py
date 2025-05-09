"""
Provides a way to define a tree of commands, used to generate a command-line interface using Click.

The `CommandTree` class is used to define the tree of commands. Each leaf in the tree represents a
command that can be executed. The nodes can have children, which represent subcommands that can be
executed under the parent command.

The `CommandServiceTree` class is used to define the tree of command using ServiceIds. The tree's
subcommands and handlers are resolved from the container, allowing lazy loading.
"""

import lazy_loader

__getattr__, __dir__, __all__ = lazy_loader.attach_stub(__name__, __file__)
