import click

from rats import apps
from ._groups import ClickGroupPlugin


class ClickExecutable(apps.Executable):
    _command: apps.ServiceProvider[click.Command]
    _plugins: apps.PluginRunner[ClickGroupPlugin]

    def __init__(
        self,
        command: apps.ServiceProvider[click.Command],
        plugins: apps.PluginRunner[ClickGroupPlugin],
    ) -> None:
        self._command = command
        self._plugins = plugins

    def execute(self) -> None:
        cmd = self._command()
        self._plugins.apply(lambda plugin: plugin.on_group_open(cmd))
        cmd()


class ClickGroup(ClickGroupPlugin):
    _group: apps.ServiceProvider[click.Group]
    _plugins: apps.PluginRunner[ClickGroupPlugin]

    def __init__(
        self,
        group: apps.ServiceProvider[click.Group],
        plugins: apps.PluginRunner[ClickGroupPlugin],
    ) -> None:
        self._group = group
        self._plugins = plugins

    def on_group_open(self, group: click.Group) -> None:
        cmd = self._group()
        self._plugins.apply(lambda plugin: plugin.on_group_open(cmd))
        group.add_command(cmd)
