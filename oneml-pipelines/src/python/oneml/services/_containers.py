import logging
from abc import abstractmethod
from functools import lru_cache
from typing import Any, Dict, Generic, Iterable, List, Protocol, Tuple, TypeVar

from ._service_id import ServiceId, ServiceType
from ._settings import SettingProvider, SettingType

logger = logging.getLogger(__name__)
Tco_ServiceType = TypeVar("Tco_ServiceType", covariant=True)


class ServiceProvider(Protocol[Tco_ServiceType]):

    @abstractmethod
    def __call__(self) -> Tco_ServiceType:
        pass


class ServiceGroupProvider(Protocol[Tco_ServiceType]):

    @abstractmethod
    def __call__(self) -> Iterable[Tco_ServiceType]:
        pass


class IProvideServices(Protocol):

    def get_service(self, service_id: ServiceId[ServiceType]) -> ServiceType:
        return self.get_service_provider(service_id)()

    @abstractmethod
    def get_service_provider(
        self,
        service_id: ServiceId[ServiceType],
    ) -> ServiceProvider[ServiceType]:
        pass

    def get_service_group(self, group_id: ServiceId[ServiceType]) -> Iterable[ServiceType]:
        logger.debug(f"Searching for group: {group_id}")
        for group in self.get_service_group_providers(group_id):
            logger.debug(group_id)
            yield group()

    @abstractmethod
    def get_service_group_providers(
        self,
        group_id: ServiceId[ServiceType],
    ) -> Iterable[ServiceProvider[ServiceType]]:
        pass


class IDefineServices(Protocol):

    def parse_service_container(self, container: Any) -> None:
        methods = [method for method in dir(container) if method.startswith('_') is False]

        for method_name in methods:
            method = getattr(container, method_name)
            if getattr(method, "__service_provider__", False):
                for service_id in method.__service_ids__:
                    self.add_service(service_id, method)

            if getattr(method, "__service_group_provider__", False):
                for service_id in method.__service_group_ids__:
                    self.add_group(service_id, method)

    def add_services(
        self,
        *services: Tuple[ServiceId[ServiceType], ServiceProvider[ServiceType]],
    ) -> None:
        for service_id, service_provider in services:
            self.add_service(service_id, service_provider)

    @abstractmethod
    def add_service(
        self,
        service_id: ServiceId[ServiceType],
        provider: ServiceProvider[ServiceType],
    ) -> None:
        pass

    def add_groups(
        self,
        *services: Tuple[ServiceId[ServiceType], ServiceProvider[ServiceType]],
    ) -> None:
        for group_id, service_provider in services:
            self.add_group(group_id, service_provider)

    @abstractmethod
    def add_group(
        self,
        group_id: ServiceId[ServiceType],
        provider: ServiceProvider[ServiceType],
    ) -> None:
        pass


class IManageServices(IProvideServices, IDefineServices, Protocol):
    pass


class ServiceFactory(IManageServices):

    _providers: Dict[ServiceId[Any], ServiceProvider[Any]]
    # TODO: would this be better as a mapping of service_id to a list of service_ids?
    #       that would require all groups to be made of existing services
    _groups: Dict[ServiceId[Any], List[ServiceProvider[Any]]]

    def __init__(self) -> None:
        self._providers = {}
        self._groups = {}

    def get_service_provider(self, service_id: ServiceId[ServiceType]) -> ServiceProvider[ServiceType]:
        # this lambda defers the checking of this key until the service is actually requested
        return lambda: self._providers[service_id]()

    def get_service_group(self, group_id: ServiceId[ServiceType]) -> Iterable[ServiceType]:
        for x in self._groups[group_id]:
            # Using a generator to defer the evaluation of the providers
            yield x()

    def get_service_group_providers(
        self,
        group_id: ServiceId[ServiceType],
    ) -> Iterable[ServiceProvider[ServiceType]]:
        return self._groups.get(group_id, tuple())

    def add_service(
        self,
        service_id: ServiceId[ServiceType],
        provider: ServiceProvider[ServiceType],
    ) -> None:
        self._providers[service_id] = provider

    def add_group(
        self,
        group_id: ServiceId[ServiceType],
        provider: ServiceProvider[ServiceType],
    ) -> None:
        group = self._groups.get(group_id, [])
        group.append(provider)
        self._groups[group_id] = group


class ServiceContainer(IProvideServices):

    _factory: IProvideServices

    def __init__(self, factory: IProvideServices) -> None:
        self._factory = factory

    def get_service_provider(self, service_id: ServiceId[ServiceType]) -> ServiceProvider[ServiceType]:
        return lambda: self.get_service(service_id)

    @lru_cache()
    def get_service(self, service_id: ServiceId[ServiceType]) -> ServiceType:
        return self._factory.get_service(service_id)

    @lru_cache()
    def get_service_group_providers(
            self,
            group_id: ServiceId[ServiceType],
    ) -> Iterable[ServiceProvider[ServiceType]]:
        return self._factory.get_service_group_providers(group_id)


class ContextualServiceContainer(IProvideServices, Generic[SettingType]):

    _container: IProvideServices
    _context: SettingProvider[SettingType]

    def __init__(self, container: IProvideServices, context: SettingProvider[SettingType]) -> None:
        self._container = container
        self._context = context

    def get_service_provider(self, service_id: ServiceId[ServiceType]) -> ServiceProvider[ServiceType]:
        return lambda: self.get_service(service_id)

    def get_service(self, service_id: ServiceId[ServiceType]) -> ServiceType:
        return self._get_cached(service_id, self._context())

    def get_service_group_providers(
            self,
            group_id: ServiceId[ServiceType],
    ) -> Iterable[ServiceProvider[ServiceType]]:
        return self._get_group_providers_cached(group_id, self._context())

    @lru_cache()
    def _get_cached(
        self,
        service_id: ServiceId[ServiceType],
        context_value: SettingType,
    ) -> ServiceType:
        return self._container.get_service(service_id)

    @lru_cache()
    def _get_group_providers_cached(
            self,
            group_id: ServiceId[ServiceType],
            context_value: SettingType,
    ) -> Iterable[ServiceProvider[ServiceType]]:
        return self._container.get_service_group_providers(group_id)


"""
Is it easier if the typed containers just take strings since the return type is denoted in the class
generic? that would break the interface but would give people a simpler API without losing
capabilities.
"""


class TypedServiceContainer(Generic[ServiceType]):

    _container: IProvideServices

    def __init__(self, container: IProvideServices) -> None:
        self._container = container

    def get_service_group_providers(self, group_name: str) -> Iterable[ServiceProvider[ServiceType]]:
        return self._container.get_service_group_providers(ServiceId[ServiceType](group_name))

    def get_service_provider(self, service_name: str) -> ServiceProvider[ServiceType]:
        return lambda: self.get_service(service_name)

    def get_service(self, service_name: str) -> ServiceType:
        return self._container.get_service(ServiceId[ServiceType](service_name))


class FilteredServiceContainer(IProvideServices):

    _container: IProvideServices
    _services: Iterable[ServiceId[Any]]

    def __init__(self, container: IProvideServices, services: Iterable[ServiceId[Any]]) -> None:
        self._container = container
        self._services = services

    def get_service_group_providers(
        self,
        group_id: ServiceId[ServiceType],
    ) -> Iterable[ServiceProvider[ServiceType]]:
        if group_id not in self._services:
            raise ValueError(f"Service {group_id} not found")

        return self._container.get_service_group_providers(group_id)

    def get_service_provider(self, service_id: ServiceId[ServiceType]) -> ServiceProvider[ServiceType]:
        if service_id not in self._services:
            raise ValueError(f"Service {service_id} not found")

        return lambda: self.get_service(service_id)

    def get_service(self, service_id: ServiceId[ServiceType]) -> ServiceType:
        if service_id not in self._services:
            raise ValueError(f"Service {service_id} not found")

        return self._container.get_service(service_id)
