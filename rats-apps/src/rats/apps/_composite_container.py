from collections.abc import Iterator
from typing import final

from ._container import Container
from ._ids import ServiceId, T_ServiceType


@final
class CompositeContainer(Container):
    _containers: tuple[Container, ...]

    def __init__(self, *containers: Container) -> None:
        self._containers = containers

    def get_namespaced_group(
        self,
        namespace: str,
        group_id: ServiceId[T_ServiceType],
    ) -> Iterator[T_ServiceType]:
        for container in self._containers:
            yield from container.get_namespaced_group(namespace, group_id)


EMPTY_CONTAINER = CompositeContainer()
"""Convenience [rats.apps.Container][] instance with no services."""
