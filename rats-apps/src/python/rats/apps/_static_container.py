from collections.abc import Callable
from typing import Iterator, NamedTuple

from rats import apps
from ._ids import ServiceId, T_ServiceType


class StaticProvider(NamedTuple):
    namespace: str
    service_id: ServiceId[T_ServiceType]
    provider: Callable[[], T_ServiceType]


class StaticContainer(apps.Container):

    _providers: tuple[StaticProvider, ...]

    def __init__(self, *providers: StaticProvider) -> None:
        self._providers = providers

    def get_namespaced_group(
        self,
        namespace: str,
        group_id: ServiceId[T_ServiceType],
    ) -> Iterator[T_ServiceType]:
        for provider in self._providers:
            if provider.namespace == namespace and provider.service_id == group_id:
                yield provider.provider()
