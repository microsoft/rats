from collections.abc import Callable

import click

# pyright seems to struggle with this namespace package
# https://github.com/microsoft/pyright/issues/2882
from rats import apps as apps
from rats import cli as cli
from rats import command_tree as command_tree
from rats import devtools as devtools

from ._commands import ComponentArgs, RatsCiCommands
from ._ids import PluginServices


class RatsCiPlugin(apps.AnnotatedContainer):
    _app: apps.Container

    def __init__(self, app: apps.Container) -> None:
        self._app = app

    @apps.group(command_tree.CommandTreeServices.GROUPS.subcommands("rats-devtools"))
    def ci_command_tree(self) -> command_tree.CommandTree:
        return command_tree.CommandTree(
            name="ci",
            description="Commands for performing continuous integration actions.",
            kwargs_class=ComponentArgs,
            children=tuple(
                (
                    child.to_command_tree(self)
                    if isinstance(child, command_tree.CommandServiceTree)
                    else child
                )
                for child in self._app.get_group(
                    command_tree.CommandTreeServices.GROUPS.subcommands("rats-devtools ci")
                )
            ),
        )

    @apps.group(devtools.AppServices.GROUPS.CLI_ROOT_COMMANDS)
    def ci_command(self) -> click.Command:
        cmds = [
            "poetry-install",
            "test",
            "build-wheel",
            "publish-wheel",
            "check-all",
        ]

        def get(name: str) -> Callable[[], click.Command]:
            return lambda: self._app.get(PluginServices.command(name))

        return cli.DeferredCommandGroup(
            name="ci",
            provider=cli.CommandProvider(
                commands={name: get(name) for name in cmds},
            ),
        )

    @apps.container()
    def ci_subcommands(self) -> apps.Container:
        return RatsCiCommands(self._app)
