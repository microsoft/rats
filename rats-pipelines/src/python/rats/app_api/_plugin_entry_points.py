import logging
from collections.abc import Iterator
from importlib.metadata import entry_points
from typing import TypeAlias, cast

from rats.services import IManageServices, ServiceProvider

from ._plugin import AppPlugin

logger = logging.getLogger(__name__)
AppPluginEntryPoint: TypeAlias = ServiceProvider[AppPlugin]


class AppEntryPointPluginRelay(AppPlugin):
    """Rats plugin that loads other plugins from python entry points."""

    _group: str

    def __init__(self, group: str) -> None:
        self._group = group

    def load_plugin(self, app: IManageServices) -> None:
        for entry in self._load_entry_points():
            try:
                instance = entry()
                instance.load_plugin(app)
            except ValueError:
                # TODO: we want to catch when the entrypoint has required args
                # This is something we failed to create an interface for
                # Proper behavior might be to try all plugins, collect all failed,
                # and raise one error
                raise

    def _load_entry_points(self) -> Iterator[AppPluginEntryPoint]:
        entries = entry_points(group=self._group)
        if len(entries) == 0:
            logger.warning(f"did not find any app plugins registered with group: {self._group}")
            return ()

        for entry in entries:
            logger.debug(f"loading app plugin entry point: {entry.name}")
            yield cast(AppPluginEntryPoint, entry.load())
