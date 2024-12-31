from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any, Generic

from ._container import Container, Provider
from ._ids import ServiceId, T_ServiceType
from ._namespaces import ProviderNamespaces


@dataclass(frozen=True)
class StaticProvider(Generic[T_ServiceType]):
    namespace: str
    service_id: ServiceId[T_ServiceType]
    call: Provider[T_ServiceType]


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
                yield provider.call()


def static_service(
    service_id: ServiceId[T_ServiceType],
    provider: Provider[T_ServiceType],
) -> StaticProvider[T_ServiceType]:
    """
    Factory function for a `StaticProvider` instance for `ProviderNamespaces.SERVICES`.

    Args:
        service_id: the identifier for the provided service.
        provider: a callable that returns an instance of T_ServiceType.

    Returns: StaticProvider instance for the provided service_id.
    """
    return StaticProvider(ProviderNamespaces.SERVICES, service_id, provider)


def static_group(
    group_id: ServiceId[T_ServiceType],
    provider: Provider[T_ServiceType],
) -> StaticProvider[T_ServiceType]:
    """
    Factory function for a `StaticProvider` instance for `ProviderNamespaces.GROUPS`.

    !!! warning
        Unlike group providers in a container, the provider function argument here should return
        a single instance of the service group.

    Args:
        group_id: the identifier for the provided service group.
        provider: a callable that returns an instance of T_ServiceType.

    Returns: StaticProvider instance for the provided group_id.
    """
    return StaticProvider(ProviderNamespaces.GROUPS, group_id, provider)
