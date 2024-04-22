from typing import Any

from rats import apps

from ._click import ClickCommandGroup, ClickCommandRegistry
from ._commands import RatsDevtoolsCommands


@apps.autoscope
class RatsDevtoolsServices:
    CLI = apps.ServiceId[apps.Executable]("cli")


class RatsDevtoolsGroups:
    COMMANDS = apps.ServiceId[ClickCommandRegistry]("commands")


class RatsDevtoolsAppContainer(apps.AnnotatedContainer):
    def get_service_ids(self) -> Any:
        raise RuntimeError("deprecated method added for backwards compatibility")

    @apps.service(RatsDevtoolsServices.CLI)
    def cli(self) -> ClickCommandGroup:
        return ClickCommandGroup(
            lambda: self.get_group(
                RatsDevtoolsGroups.COMMANDS,
            )
        )

    @apps.group(RatsDevtoolsGroups.COMMANDS)
    def commands(self) -> RatsDevtoolsCommands:
        return RatsDevtoolsCommands()

    @apps.container()
    def plugins(self) -> apps.Container:
        return apps.PluginContainers(self, "rats.devtools.plugins")


def run() -> None:
    container = RatsDevtoolsAppContainer()
    container.get(RatsDevtoolsServices.CLI).execute()
