from collections.abc import Callable

import click

# pyright seems to struggle with this namespace package
# https://github.com/microsoft/pyright/issues/2882
from rats import apps as apps
from rats import cli as cli
from rats import devtools as devtools

from ._commands import RatsCiCommands
from ._ids import PluginServices


class RatsDocsPlugin(apps.AnnotatedContainer):
    _app: apps.Container

    def __init__(self, app: apps.Container) -> None:
        self._app = app

    @apps.group(devtools.AppServices.GROUPS.CLI_ROOT_COMMANDS)
    def docs_command(self) -> click.Command:
        cmds = [
            "mkdocs-serve",
            "mkdocs-build",
            "sphinx-build",
            "build-tutorial-notebooks",
        ]

        def get(name: str) -> Callable[[], click.Command]:
            return lambda: self._app.get(PluginServices.command(name))

        return cli.DeferredCommandGroup(
            name="docs",
            provider=cli.CommandProvider(
                commands={name: get(name) for name in cmds},
            ),
        )

    @apps.container()
    def ci_subcommands(self) -> apps.Container:
        return RatsCiCommands(self._app)
