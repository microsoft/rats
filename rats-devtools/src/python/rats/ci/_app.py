from rats import apps, devtools  # type: ignore[reportAttributeAccessIssue]

from ._commands import RatsCiCommands


@apps.autoscope
class RatsCiServices:
    CLI = apps.ServiceId[apps.Executable]("cli")


class RatsCiGroups:
    COMMANDS = apps.ServiceId[devtools.ClickCommandRegistry]("pycharm-commands")


class RatsCiPlugin(apps.AnnotatedContainer):
    _app: apps.Container

    def __init__(self, app: apps.Container) -> None:
        self._app = app

    @apps.service(RatsCiServices.CLI)
    def cli(self) -> apps.Executable:
        return devtools.ClickCommandGroup(
            lambda: self._app.get_group(
                RatsCiGroups.COMMANDS,
            )
        )

    @apps.group(devtools.RatsDevtoolsGroups.COMMANDS)
    @apps.group(RatsCiGroups.COMMANDS)
    def commands(self) -> RatsCiCommands:
        return RatsCiCommands()


def run() -> None:
    app = apps.AppContainer(lambda app: RatsCiPlugin(app))
    app.get(RatsCiServices.CLI).execute()
