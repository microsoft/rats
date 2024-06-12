from dataclasses import dataclass
from typing import Annotated

import click

# pyright seems to struggle with this namespace package
# https://github.com/microsoft/pyright/issues/2882
from rats import apps as apps
from rats import cli as cli
from rats import command_tree as command_tree
from rats import devtools as devtools

from ._formatter import FileFormatter, FileFormatterRequest


@dataclass(frozen=True)
class AutoformatterArgs:
    """Arguments for the autoformatter command."""

    filename: Annotated[
        str,
        command_tree.ClickConversion(
            argument=True,
            explicit_click_type=click.Path(exists=True, file_okay=True, dir_okay=False),
        ),
    ]
    """The filename to format."""


class RatsPycharmCommandTreePlugin(apps.Container):
    _app: apps.Container

    def __init__(self, app: apps.Container) -> None:
        self._app = app

    @apps.group(command_tree.CommandTreeServices.GROUPS.subcommands("rats-devtools"))
    def pycharm_command_tree(self) -> command_tree.CommandTree:
        return command_tree.CommandTree(
            name="pycharm",
            description="Commands for managing PyCharm configuration.",
            children=tuple(
                (
                    child.to_command_tree(self)
                    if isinstance(child, command_tree.CommandServiceTree)
                    else child
                )
                for child in self._app.get_group(
                    command_tree.CommandTreeServices.GROUPS.subcommands("rats-devtools pycharm")
                )
            ),
        )

    @apps.group(command_tree.CommandTreeServices.GROUPS.subcommands("rats-devtools pycharm"))
    def apply_auto_formatters_command_tree(self) -> command_tree.CommandTree:
        def handler(autoformatter_args: AutoformatterArgs) -> None:
            formatter = FileFormatter(
                request=lambda: FileFormatterRequest(autoformatter_args.filename)
            )
            formatter.execute()

        return command_tree.CommandTree(
            name="apply-auto-formatters",
            description="Apply auto formatters to a file.",
            handler=handler,
        )
