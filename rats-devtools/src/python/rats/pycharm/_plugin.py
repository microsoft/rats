from collections.abc import Callable
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
    filename: Annotated[str, command_tree.ClickConversion(argument=True)]


@apps.autoscope
class PluginServices:
    @staticmethod
    def command(name: str) -> apps.ServiceId[click.Command]:
        return apps.ServiceId(f"cli-commands[{name}]")


class RatsPycharmPlugin(apps.AnnotatedContainer):
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

    @apps.group(devtools.AppServices.GROUPS.CLI_ROOT_COMMANDS)
    def pycharm_command(self) -> click.Command:
        cmds = [
            "apply-auto-formatters",
        ]

        def get(name: str) -> Callable[[], click.Command]:
            return lambda: self._app.get(PluginServices.command(name))

        return cli.DeferredCommandGroup(
            name="pycharm",
            provider=cli.CommandProvider(
                commands={name: get(name) for name in cmds},
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

    @apps.service(PluginServices.command("apply-auto-formatters"))
    def apply_auto_formatters(self) -> click.Command:
        @click.argument(
            "filename",
            type=click.Path(exists=True, file_okay=True, dir_okay=False),
        )
        def run(filename: str) -> None:
            formatter = FileFormatter(request=lambda: FileFormatterRequest(filename))
            formatter.execute()

        return click.Command(
            name="apply-auto-formatters",
            callback=run,
            params=list(reversed(getattr(run, "__click_params__", []))),
            help="Help for apply-auto-formatters",
            short_help="Short help for apply-auto-formatters",
        )
