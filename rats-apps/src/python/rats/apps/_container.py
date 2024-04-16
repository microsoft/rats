from abc import abstractmethod
from collections.abc import Iterator
from typing import Generic, Protocol

from ._ids import ServiceId, T_ServiceType, Tco_ConfigType, Tco_ServiceType
from ._namespaces import ProviderNamespaces


class ServiceProvider(Protocol[Tco_ServiceType]):
    @abstractmethod
    def __call__(self) -> Tco_ServiceType:
        """Return the service instance."""


class ConfigProvider(ServiceProvider[Tco_ConfigType], Protocol[Tco_ConfigType]):
    @abstractmethod
    def __call__(self) -> Tco_ConfigType:
        """Return the config instance."""


class Container(Protocol):
    """Main interface for service containers."""

    def has(self, service_id: ServiceId[T_ServiceType]) -> bool:
        try:
            return self.get(service_id) is not None
        except ServiceNotFoundError:
            return False

    def has_group(self, group_id: ServiceId[T_ServiceType]) -> bool:
        try:
            return next(self.get_group(group_id)) is not None
        except StopIteration:
            return False

    def has_namespace(self, namespace: str, group_id: ServiceId[T_ServiceType]) -> bool:
        try:
            return next(self.get_namespaced_group(namespace, group_id)) is not None
        except StopIteration:
            return False

    def get(self, service_id: ServiceId[T_ServiceType]) -> T_ServiceType:
        """Retrieve a service instance by its id."""
        services = list(self.get_namespaced_group(ProviderNamespaces.SERVICES, service_id))
        if len(services) == 0:
            services.extend(
                list(self.get_namespaced_group(ProviderNamespaces.FALLBACK_SERVICES, service_id)),
            )

        if len(services) > 1:
            raise DuplicateServiceError(service_id)
        elif len(services) == 0:
            raise ServiceNotFoundError(service_id)
        else:
            return services[0]

    def get_group(
        self,
        group_id: ServiceId[T_ServiceType],
    ) -> Iterator[T_ServiceType]:
        """Retrieve a service group by its id."""
        if not self.has_namespace(ProviderNamespaces.GROUPS, group_id):
            yield from self.get_namespaced_group(ProviderNamespaces.FALLBACK_GROUPS, group_id)

        yield from self.get_namespaced_group(ProviderNamespaces.GROUPS, group_id)

    @abstractmethod
    def get_namespaced_group(
        self,
        namespace: str,
        group_id: ServiceId[T_ServiceType],
    ) -> Iterator[T_ServiceType]:
        """Retrieve a service group by its id, within a given service namespace."""


class ServiceNotFoundError(RuntimeError, Generic[T_ServiceType]):
    service_id: ServiceId[T_ServiceType]

    def __init__(self, service_id: ServiceId[T_ServiceType]) -> None:
        super().__init__(f"Service id not found: {service_id}")
        self.service_id = service_id


class DuplicateServiceError(RuntimeError, Generic[T_ServiceType]):
    service_id: ServiceId[T_ServiceType]

    def __init__(self, service_id: ServiceId[T_ServiceType]) -> None:
        super().__init__(f"Service id provided multiple times: {service_id}")
        self.service_id = service_id
