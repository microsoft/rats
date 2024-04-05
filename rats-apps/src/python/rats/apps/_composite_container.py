from collections.abc import Iterator

from ._container import Container
from ._ids import ServiceId, T_ServiceType


class CompositeContainer(Container):
    _contailers: tuple[Container, ...]

    def __init__(self, *containers: Container) -> None:
        self._containers = containers

    def get_namespace(
        self,
        namespace: ServiceId[T_ServiceType],
        group_id: ServiceId[T_ServiceType],
    ) -> Iterator[T_ServiceType]:
        for container in self._containers:
            yield from container.get_namespace(namespace, group_id)
