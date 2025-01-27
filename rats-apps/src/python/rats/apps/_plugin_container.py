from collections.abc import Iterable, Iterator
from functools import cache
from importlib.metadata import entry_points

from ._container import Container
from ._ids import ServiceId, T_ServiceType


class PythonEntryPointContainer(Container):
    """
    A container that loads plugins using [importlib.metadata.entry_points][].

    When looking for groups, the container loads the specified entry_points and defers the lookups
    to the plugins. Plugin containers are expected to be Callable[[Container], Container] objects,
    where the input container is typically the root application container.

    TODO: How do we better specify the API for plugins without relying on documentation?
    """

    _app: Container
    _group: str
    _names: tuple[str, ...]

    def __init__(self, app: Container, group: str, *names: str) -> None:
        self._app = app
        self._group = group
        self._names = names

    def get_namespaced_group(
        self,
        namespace: str,
        group_id: ServiceId[T_ServiceType],
    ) -> Iterator[T_ServiceType]:
        for container in self._load_containers():
            yield from container.get_namespaced_group(namespace, group_id)

    @cache  # noqa: B019
    def _load_containers(self) -> Iterable[Container]:
        entries = entry_points(group=self._group)
        return tuple(entry.load()(self._app) for entry in entries if self._is_enabled(entry.name))

    def _is_enabled(self, plugin_name: str) -> bool:
        return len(self._names) == 0 or plugin_name in self._names
