from collections.abc import Callable, Iterator
from typing import Any, Generic

from typing_extensions import NamedTuple as ExtNamedTuple

from ._container import Container
from ._ids import ServiceId, T_ServiceType


class StaticProvider(ExtNamedTuple, Generic[T_ServiceType]):
    namespace: str
    service_id: ServiceId[T_ServiceType]
    provider: Callable[[], T_ServiceType]


class StaticContainer(Container):
    _providers: tuple[StaticProvider[Any], ...]

    def __init__(self, *providers: StaticProvider[Any]) -> None:
        self._providers = providers

    def get_namespaced_group(
        self,
        namespace: str,
        group_id: ServiceId[T_ServiceType],
    ) -> Iterator[T_ServiceType]:
        for provider in self._providers:
            if provider.namespace == namespace and provider.service_id == group_id:
                yield provider.provider()
