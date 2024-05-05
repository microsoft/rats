import click

# pyright seems to struggle with this namespace package
# https://github.com/microsoft/pyright/issues/2882
from rats import apps as apps
from rats import cli as cli
from rats import devtools as devtools

from ._commands import RatsCiCommands


class RatsDocsPlugin(apps.AnnotatedContainer):
    _app: apps.Container

    def __init__(self, app: apps.Container) -> None:
        self._app = app

    @apps.group(devtools.AppServices.GROUPS.CLI_ROOT_PLUGINS)
    def docs_command(self) -> cli.AttachClickGroup:
        return cli.AttachClickGroup(
            group=lambda: click.Group("docs"),
            plugins=apps.PluginRunner(
                iter([RatsCiCommands()]),
            ),
        )
