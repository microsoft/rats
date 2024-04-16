from collections.abc import Iterable, Iterator
from functools import cache
from importlib.metadata import entry_points

from ._container import Container
from ._ids import ServiceId, T_ServiceType


class PluginContainers(Container):
    _app: Container
    _group: str

    def __init__(self, app: Container, group: str) -> None:
        self._app = app
        self._group = group

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
        return tuple(entry.load()(self._app) for entry in entries)
