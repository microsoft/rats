from abc import abstractmethod
from collections.abc import Iterator
from typing import Generic, Protocol, cast

from ._categories import ProviderCategories
from ._ids import ConfigId, ServiceId, T_ConfigType, T_ServiceType


class ServiceProvider(Protocol[T_ServiceType]):

    @abstractmethod
    def __call__(self) -> T_ServiceType:
        """Return the service instance."""


class ConfigProvider(ServiceProvider[T_ConfigType], Protocol):

    @abstractmethod
    def __call__(self) -> T_ConfigType:
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

    def has_config(self, config_id: ConfigId[T_ConfigType]) -> bool:
        try:
            return self.get_config(config_id) is not None
        except ServiceNotFoundError:
            return False

    def has_category(self, category_id: ServiceId[T_ServiceType], group_id: ServiceId[T_ServiceType]) -> bool:
        try:
            return next(self.get_category(category_id, group_id)) is not None
        except StopIteration:
            return False

    def get(self, service_id: ServiceId[T_ServiceType]) -> T_ServiceType:
        """Retrieve a service instance by its id."""
        services = list(self.get_category(ProviderCategories.SERVICE, service_id))
        if len(services) == 0:
            services.extend(
                list(self.get_category(ProviderCategories.FALLBACK_SERVICE, service_id)),
            )

        if len(services) > 1:
            raise DuplicateServiceError(service_id)
        elif len(services) == 0:
            raise ServiceNotFoundError(service_id)
        else:
            return cast(T_ServiceType, services[0])

    def get_group(
        self,
        group_id: ServiceId[T_ServiceType],
    ) -> Iterator[T_ServiceType]:
        """Retrieve a service group by its id."""
        if not self.has_category(ProviderCategories.GROUP, group_id):
            yield from self.get_category(ProviderCategories.FALLBACK_GROUP, group_id)

        yield from self.get_category(ProviderCategories.GROUP, group_id)

    def get_config(self, config_id: ConfigId[T_ConfigType]) -> T_ConfigType:
        """Retrieve a config by its id."""
        services = list(self.get_category(ProviderCategories.CONFIG, config_id))
        if len(services) == 0:
            services.extend(
                list(self.get_category(ProviderCategories.FALLBACK_CONFIG, config_id)),
            )

        if len(services) > 1:
            raise DuplicateServiceError(config_id)
        elif len(services) == 0:
            raise ServiceNotFoundError(config_id)
        else:
            return cast(T_ConfigType, services[0])

    @abstractmethod
    def get_category(
        self,
        category_id: ServiceId[T_ServiceType],
        group_id: ServiceId[T_ServiceType],
    ) -> Iterator[T_ServiceType]:
        """Retrieve a service group by its id, within a given service category."""


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
