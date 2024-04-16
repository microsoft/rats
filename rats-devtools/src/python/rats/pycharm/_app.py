from collections.abc import Callable
from typing import Any, Protocol

from rats import apps
from rats.devtools._app import RatsDevtoolsAppServices
from rats.devtools._click import ClickCommandRegistry
from rats.devtools._commands import RatsDevtoolsCli, RatsDevtoolsCommands


class PluginAction(Protocol):
    def run(self) -> None: ...


class PycharmApp(apps.AnnotatedContainer):
    _plugins: tuple[Callable[[apps.Container], apps.Container], ...]

    def __init__(self, *plugins: Callable[[apps.Container], apps.Container]):
        self._plugins = plugins

    @apps.container()
    def _runtime_plugins(self) -> apps.Container:
        return apps.CompositeContainer(*[p(self) for p in self._plugins])

    @apps.container()
    def _package_plugins(self) -> apps.Container:
        return apps.PluginContainers(self, "rats-devtools.app-plugins")


@apps.autoscope
class PycharmAppServices:
    CLI = apps.ServiceId[PluginAction]("cli")


class RatsDevtoolsAppServiceGroups:
    COMMANDS = apps.ServiceId[ClickCommandRegistry]("commands")


class RatsDevtoolsAppContainer(apps.AnnotatedContainer):
    def get_service_ids(self) -> Any:
        raise RuntimeError("deprecated method added for backwards compatibility")

    @apps.service(RatsDevtoolsAppServices.CLI)
    def cli(self) -> RatsDevtoolsCli:
        return RatsDevtoolsCli(lambda: self.get_group(RatsDevtoolsAppServiceGroups.COMMANDS))

    @apps.group(RatsDevtoolsAppServiceGroups.COMMANDS)
    def commands(self) -> RatsDevtoolsCommands:
        return RatsDevtoolsCommands()


def run() -> None:
    container = RatsDevtoolsAppContainer()
    container.get(RatsDevtoolsAppServices.CLI).execute()
