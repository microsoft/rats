import logging
from abc import abstractmethod
from importlib.metadata import entry_points
from typing import Iterator, Protocol, TypeAlias, cast

from oneml.services import IManageServices, ServiceProvider

logger = logging.getLogger(__name__)


class OnemlAppPlugin(Protocol):

    @abstractmethod
    def load_plugin(self, app: IManageServices) -> None:
        pass


class OnemlPlugin(Protocol):

    @abstractmethod
    def load_plugin(self) -> None:
        pass


OnemlAppPluginEntryPoint: TypeAlias = ServiceProvider[OnemlAppPlugin]


class OnemlAppNoopPlugin(OnemlAppPlugin):

    def load_plugin(self, app: IManageServices) -> None:
        logger.debug(f"no-op plugin activating for app: {app}")


class OnemlAppEntryPointPluginRelay(OnemlAppPlugin):
    """
    Oneml plugin that loads other plugins from python entry points.
    """

    _group: str

    def __init__(self, group: str) -> None:
        self._group = group

    def load_plugin(self, app: IManageServices) -> None:
        for entry in self._load_entry_points():
            try:
                instance = entry()
                instance.load_plugin(app)
            except ValueError as e:
                # TODO: we want to catch when the entrypoint has required args
                # This is something we failed to create an interface for
                # Proper behavior might be to try all plugins, collect all failed,
                # and raise one error
                raise

    def _load_entry_points(self) -> Iterator[OnemlAppPluginEntryPoint]:
        entries = entry_points(group=self._group)
        if len(entries) == 0:
            logger.warning(f"did not find any app plugins registered with group: {self._group}")
            return tuple()

        for entry in entries:
            logger.debug(f"loading app plugin entry point: {entry.name}")
            yield cast(OnemlAppPluginEntryPoint, entry.load())
