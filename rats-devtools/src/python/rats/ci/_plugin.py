import click

from rats import apps, devtools  # type: ignore[reportAttributeAccessIssue]

from ._commands import RatsCiCommands
from ._ids import PluginServices


class RatsCiPlugin(apps.AnnotatedContainer):
    _app: apps.Container

    def __init__(self, app: apps.Container) -> None:
        self._app = app

    @apps.group(devtools.AppServices.GROUPS.CLI_ROOT_COMMANDS)
    def ci_command(self) -> click.Command:
        provider = devtools.CommandProvider(
            command_names=frozenset(
                [
                    "poetry-install",
                    "test",
                    "build-wheel",
                    "publish-wheel",
                    "check-all",
                ]
            ),
            service_mapper=lambda name: PluginServices.GROUPS.command(name),
            container=self,
        )

        return devtools.LazyClickGroup(
            name="ci",
            provider=provider,
        )

    @apps.container()
    def ci_subcommands(self) -> apps.Container:
        return RatsCiCommands(self._app)
