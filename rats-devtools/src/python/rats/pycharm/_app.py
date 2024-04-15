from typing import Any

from rats import apps

from ._click import ClickCommandRegistry
from ._commands import RatsDevtoolsCli, RatsDevtoolsCommands
from ._container import DecoratedServiceProvider


class PluginAction(Protocol):
    def run(self) -> None: ...


class PycharmApp(apps.AnnotatedContainer):
    _plugins: tuple[Callable[[Container], Container], ...]

    def __init__(self, *plugins: Callable[[Container], Container]):
        self._plugins = plugins

    @apps.container()
    def _runtime_plugins(self) -> Container:
        return CompositeContainer(*[p(self) for p in self._plugins])

    @apps.container()
    def _package_plugins(self) -> Container:
        return PluginContainers(self, "rats-devtools.app-plugins")


@apps.autoscope
class PycharmAppServices:
    CLI = ServiceId[PluginAction]("cli")


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
