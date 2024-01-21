from typing import Any

from oneml.services import (
    IExecutable, ServiceContainer,
    ServiceId,
    scoped_service_ids, service_group,
    service_provider,
)

from ._commands import OnemlDevtoolsCli, OnemlDevtoolsCommands
from ._container import DecoratedServiceProvider


@scoped_service_ids
class OnemlDevtoolsAppServices:
    CLI = ServiceId[IExecutable]("cli")


class OnemlDevtoolsAppServiceGroups:
    COMMANDS = ServiceId[OnemlDevtoolsCommands]("commands")


class OnemlDevtoolsAppContainer(DecoratedServiceProvider):

    def get_service_ids(self) -> Any:
        raise RuntimeError("deprecated method added for backwards compatibility")

    @service_provider(OnemlDevtoolsAppServices.CLI)
    def cli(self) -> OnemlDevtoolsCli:
        return OnemlDevtoolsCli(self.get_service_group_provider(
            OnemlDevtoolsAppServiceGroups.COMMANDS,
        ))

    @service_group(OnemlDevtoolsAppServiceGroups.COMMANDS)
    def commands(self) -> OnemlDevtoolsCommands:
        return OnemlDevtoolsCommands()


def run() -> None:
    container = ServiceContainer(OnemlDevtoolsAppContainer())
    container.get_service(OnemlDevtoolsAppServices.CLI).execute()
