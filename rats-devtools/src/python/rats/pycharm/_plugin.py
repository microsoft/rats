import click

# pyright seems to struggle with this namespace package
# https://github.com/microsoft/pyright/issues/2882
from rats import apps as apps
from rats import cli as cli
from rats import devtools as devtools

from ._commands import PycharmCommands


@apps.autoscope
class PluginGroups:
    PYCHARM_COMMAND_PLUGINS = apps.ServiceId[cli.ClickGroupPlugin]("cli-plugins[pycharm]")


@apps.autoscope
class PluginServices:
    @staticmethod
    def command(name: str) -> apps.ServiceId[click.Command]:
        return apps.ServiceId(f"cli-commands[{name}]")

    GROUPS = PluginGroups


class RatsPycharmPlugin(apps.Container):
    _app: apps.Container

    def __init__(self, app: apps.Container) -> None:
        self._app = app

    @apps.group(devtools.AppServices.GROUPS.CLI_ROOT_PLUGINS)
    def pycharm_command(self) -> cli.ClickGroupPlugin:
        return cli.AttachClickGroup(
            group=lambda: click.Group("pycharm"),
            plugins=apps.PluginRunner(
                iter([PycharmCommands()]),
            ),
        )
