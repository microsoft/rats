from typing import Any

from rats import apps

from ._click import ClickCommandRegistry
from ._commands import RatsDevtoolsCli, RatsDevtoolsCommands


@apps.autoscope
class RatsDevtoolsAppServices:
    CLI = apps.ServiceId[apps.Executable]("cli")


class RatsDevtoolsAppServiceGroups:
    COMMANDS = apps.ServiceId[ClickCommandRegistry]("commands")


class RatsDevtoolsAppContainer(apps.AnnotatedContainer):
    def get_service_ids(self) -> Any:
        raise RuntimeError("deprecated method added for backwards compatibility")

    @apps.service(RatsDevtoolsAppServices.CLI)
    def cli(self) -> RatsDevtoolsCli:
        return RatsDevtoolsCli(
            lambda: self.get_group(
                RatsDevtoolsAppServiceGroups.COMMANDS,
            )
        )

    @apps.group(RatsDevtoolsAppServiceGroups.COMMANDS)
    def commands(self) -> RatsDevtoolsCommands:
        return RatsDevtoolsCommands()


def run() -> None:
    container = RatsDevtoolsAppContainer()
    container.get(RatsDevtoolsAppServices.CLI).execute()
