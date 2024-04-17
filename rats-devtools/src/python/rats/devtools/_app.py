from typing import Any

from rats import apps

from ._click import ClickCommandRegistry
from ._commands import RatsDevtoolsCli, RatsDevtoolsCommands
from ._container import DecoratedServiceProvider


@apps.autoscope
class RatsDevtoolsAppServices:
    CLI = apps.ServiceId[apps.Executable]("cli")


class RatsDevtoolsAppServiceGroups:
    COMMANDS = apps.ServiceId[ClickCommandRegistry]("commands")


class RatsDevtoolsAppContainer(DecoratedServiceProvider):
    def get_service_ids(self) -> Any:
        raise RuntimeError("deprecated method added for backwards compatibility")

    @apps.service(RatsDevtoolsAppServices.CLI)
    def cli(self) -> RatsDevtoolsCli:
        return RatsDevtoolsCli(
            self.get_service_group_provider(
                RatsDevtoolsAppServiceGroups.COMMANDS,
            )
        )

    @apps.group(RatsDevtoolsAppServiceGroups.COMMANDS)
    def commands(self) -> RatsDevtoolsCommands:
        return RatsDevtoolsCommands()


def run() -> None:
    container = RatsDevtoolsAppContainer()
    container.get_service(RatsDevtoolsAppServices.CLI).execute()
