import click

from rats import apps, cli

from ._ids import AppServices


class DevtoolsCliPlugin(apps.AnnotatedContainer):
    _app: apps.Container

    def __init__(self, app: apps.Container) -> None:
        self._app = app

    @apps.service(AppServices.CLI_EXE)
    def cli_exe(self) -> apps.Executable:
        return cli.ClickExecutable(
            command=lambda: click.Group(),
            plugins=apps.PluginRunner(self._app.get_group(AppServices.GROUPS.CLI_ROOT_PLUGINS)),
        )

    @apps.group(AppServices.GROUPS.CLI_ROOT_PLUGINS)
    def root_commands_plugin(self) -> cli.AttachGroupCommands:
        return cli.AttachGroupCommands(self._app.get_group(AppServices.GROUPS.CLI_ROOT_COMMANDS))
