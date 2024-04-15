from typing import Any

from rats import apps

from ._click import ClickCommandRegistry
from ._commands import RatsDevtoolsCli, RatsDevtoolsCommands
from ._container import DecoratedServiceProvider


class PycharmApp:
    def __init__(self, plugins: Iterable[apps.Container]) -> None:
        self._plugins = plugins

    def run(self) -> None:
        pass


@scoped_service_ids
class RatsDevtoolsAppServices:
    CLI = ServiceId[Any]("cli")


class RatsDevtoolsAppServiceGroups:
    COMMANDS = ServiceId[ClickCommandRegistry]("commands")


class RatsDevtoolsAppContainer(DecoratedServiceProvider):
    def get_service_ids(self) -> Any:
        raise RuntimeError("deprecated method added for backwards compatibility")

    @service_provider(RatsDevtoolsAppServices.CLI)
    def cli(self) -> RatsDevtoolsCli:
        return RatsDevtoolsCli(
            self.get_service_group_provider(
                RatsDevtoolsAppServiceGroups.COMMANDS,
            )
        )

    @service_group(RatsDevtoolsAppServiceGroups.COMMANDS)
    def commands(self) -> RatsDevtoolsCommands:
        return RatsDevtoolsCommands()


def run() -> None:
    container = ServiceContainer(RatsDevtoolsAppContainer())
    container.get_service(RatsDevtoolsAppServices.CLI).execute()
