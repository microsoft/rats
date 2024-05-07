import click

from rats import apps

from ._plugins import ClickGroupPlugin


class ClickExecutable(apps.Executable):
    _command: apps.ServiceProvider[click.Group]
    _plugins: apps.PluginRunner[ClickGroupPlugin]

    def __init__(
        self,
        command: apps.ServiceProvider[click.Group],
        plugins: apps.PluginRunner[ClickGroupPlugin],
    ) -> None:
        self._command = command
        self._plugins = plugins

    def execute(self) -> None:
        cmd = self._command()
        self._plugins.apply(lambda plugin: plugin.on_group_open(cmd))
        cmd()
