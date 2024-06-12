import click

from rats import apps, cli

from ._ids import AppServices


class DevtoolsCliPlugin(apps.Container):
    """
    Plugin that provides the root cli experience for rats-devtools.

    This package doesn't include any commands on its own, but it provides a plugin for others to
    create and attach subcommands to the `rats-devtools` command.
    """

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
    def root_commands_plugin(self) -> cli.AttachClickCommands:
        return cli.AttachClickCommands(self._app.get_group(AppServices.GROUPS.CLI_ROOT_COMMANDS))
