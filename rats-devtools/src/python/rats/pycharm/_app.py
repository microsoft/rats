from rats import apps, devtools  # type: ignore[reportAttributeAccessIssue]

from ._commands import RatsPycharmCommands


@apps.autoscope
class RatsPycharmServices:
    CLI = apps.ServiceId[apps.Executable]("cli")


class RatsPycharmGroups:
    COMMANDS = apps.ServiceId[devtools.ClickCommandRegistry]("pycharm-commands")


class RatsPycharmPlugin(apps.AnnotatedContainer):
    _app: apps.Container

    def __init__(self, app: apps.Container) -> None:
        self._app = app

    @apps.service(RatsPycharmServices.CLI)
    def cli(self) -> apps.Executable:
        return devtools.ClickCommandGroup(
            lambda: self._app.get_group(
                RatsPycharmGroups.COMMANDS,
            )
        )

    @apps.group(devtools.RatsDevtoolsGroups.COMMANDS)
    @apps.group(RatsPycharmGroups.COMMANDS)
    def commands(self) -> RatsPycharmCommands:
        return RatsPycharmCommands()


def run() -> None:
    app = apps.AppContainer(lambda app: RatsPycharmPlugin(app))
    app.get(RatsPycharmServices.CLI).execute()
