from collections.abc import Iterable
from functools import lru_cache
from typing import Any, Generic

from ._contexts import ContextProvider, T_ContextType
from ._service_managers import IProvideServices
from ._services import ServiceId, ServiceProvider, T_ServiceType


class ServiceContainer(IProvideServices):
    _factory: IProvideServices
    _service_cache: dict[ServiceId[Any], Any]

    def __init__(self, factory: IProvideServices) -> None:
        self._factory = factory
        self._service_cache = {}

    def get_service_provider(
        self, service_id: ServiceId[T_ServiceType]
    ) -> ServiceProvider[T_ServiceType]:
        return lambda: self.get_service(service_id)

    def get_service(self, service_id: ServiceId[T_ServiceType]) -> T_ServiceType:
        if service_id not in self._service_cache:
            self._service_cache[service_id] = self._factory.get_service(service_id)

        return self._service_cache[service_id]

    @lru_cache  # noqa: B019
    def get_service_group_provider(  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        group_id: ServiceId[T_ServiceType],
    ) -> ServiceProvider[Iterable[T_ServiceType]]:
        return self._factory.get_service_group_provider(group_id)

    @lru_cache  # noqa: B019
    def get_service_group_providers(  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        group_id: ServiceId[T_ServiceType],
    ) -> Iterable[ServiceProvider[T_ServiceType]]:
        return self._factory.get_service_group_providers(group_id)


class ContextualServiceContainer(IProvideServices, Generic[T_ContextType]):
    _container: IProvideServices
    _context_provider: ContextProvider[T_ContextType]

    def __init__(
        self,
        container: IProvideServices,
        context_provider: ContextProvider[T_ContextType],
    ) -> None:
        self._container = container
        self._context_provider = context_provider

    def get_service_provider(
        self, service_id: ServiceId[T_ServiceType]
    ) -> ServiceProvider[T_ServiceType]:
        return lambda: self.get_service(service_id)

    def get_service(self, service_id: ServiceId[T_ServiceType]) -> T_ServiceType:
        return self._get_cached(service_id, self._context_provider())

    def get_service_group_provider(
        self,
        group_id: ServiceId[T_ServiceType],
    ) -> ServiceProvider[Iterable[T_ServiceType]]:
        return self._get_group_provider_cached(group_id, self._context_provider())

    def get_service_group_providers(
        self,
        group_id: ServiceId[T_ServiceType],
    ) -> Iterable[ServiceProvider[T_ServiceType]]:
        return self._get_group_providers_cached(group_id, self._context_provider())

    @lru_cache  # noqa: B019
    def _get_cached(
        self,
        service_id: ServiceId[T_ServiceType],
        context_value: T_ContextType,
    ) -> T_ServiceType:
        return self._container.get_service(service_id)

    @lru_cache  # noqa: B019
    def _get_group_provider_cached(
        self,
        group_id: ServiceId[T_ServiceType],
        context_value: T_ContextType,
    ) -> ServiceProvider[Iterable[T_ServiceType]]:
        return self._container.get_service_group_provider(group_id)

    @lru_cache  # noqa: B019
    def _get_group_providers_cached(
        self,
        group_id: ServiceId[T_ServiceType],
        context_value: T_ContextType,
    ) -> Iterable[ServiceProvider[T_ServiceType]]:
        return self._container.get_service_group_providers(group_id)
