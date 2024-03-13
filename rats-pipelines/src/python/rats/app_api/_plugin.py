from abc import abstractmethod
from asyncio import Protocol

from rats.services import IExecutable, IManageServices, ServiceGroupProvider


class AppPlugin(Protocol):
    @abstractmethod
    def load_plugin(self, app: IManageServices) -> None:
        pass


class InitializePluginsExe(IExecutable):
    _app: IManageServices
    _group: ServiceGroupProvider[AppPlugin]

    def __init__(self, app: IManageServices, group: ServiceGroupProvider[AppPlugin]) -> None:
        self._app = app
        self._group = group

    def execute(self) -> None:
        for plugin in self._group():
            plugin.load_plugin(self._app)
