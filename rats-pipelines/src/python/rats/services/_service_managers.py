import logging
from abc import abstractmethod
from collections.abc import Iterable
from typing import Generic, Protocol

from ._services import ServiceId, ServiceProvider, T_ServiceType

logger = logging.getLogger(__name__)


class IProvideServices(Protocol):
    def get_service(self, service_id: ServiceId[T_ServiceType]) -> T_ServiceType:
        return self.get_service_provider(service_id)()

    @abstractmethod
    def get_service_provider(
        self,
        service_id: ServiceId[T_ServiceType],
    ) -> ServiceProvider[T_ServiceType]: ...

    def get_service_group(self, group_id: ServiceId[T_ServiceType]) -> Iterable[T_ServiceType]:
        logger.debug(f"Searching for group: {group_id}")
        for group in self.get_service_group_providers(group_id):
            logger.debug(group_id)
            yield group()

    @abstractmethod
    def get_service_group_provider(
        self,
        group_id: ServiceId[T_ServiceType],
    ) -> ServiceProvider[Iterable[T_ServiceType]]: ...

    @abstractmethod
    def get_service_group_providers(
        self,
        group_id: ServiceId[T_ServiceType],
    ) -> Iterable[ServiceProvider[T_ServiceType]]: ...


class IDefineServices(Protocol):
    def parse_service_container(self, instance: object) -> None:
        methods = [method for method in dir(instance) if not method.startswith("_")]

        for method_name in methods:
            method = getattr(instance, method_name)
            if getattr(method, "__service_provider__", False):
                for service_id in method.__service_ids__:
                    self.add_service(service_id, method)

            if getattr(method, "__service_group_provider__", False):
                for service_id in method.__service_group_ids__:
                    self.add_group(service_id, method)

    def add_services(
        self,
        *services: tuple[ServiceId[T_ServiceType], ServiceProvider[T_ServiceType]],
    ) -> None:
        for service_id, service_provider in services:
            self.add_service(service_id, service_provider)

    @abstractmethod
    def add_service(
        self,
        service_id: ServiceId[T_ServiceType],
        provider: ServiceProvider[T_ServiceType],
    ) -> None: ...

    def add_groups(
        self,
        *services: tuple[ServiceId[T_ServiceType], ServiceProvider[T_ServiceType]],
    ) -> None:
        for group_id, service_provider in services:
            self.add_group(group_id, service_provider)

    @abstractmethod
    def add_group(
        self,
        group_id: ServiceId[T_ServiceType],
        provider: ServiceProvider[T_ServiceType],
    ) -> None: ...


class IManageServices(IProvideServices, IDefineServices, Protocol):
    pass


class DuplicateServiceIdError(RuntimeError, Generic[T_ServiceType]):
    service_id: ServiceId[T_ServiceType]

    def __init__(self, service_id: ServiceId[T_ServiceType]) -> None:
        super().__init__(f"Duplicate service id: {service_id}")
        self.service_id = service_id


class ServiceIdNotFoundError(RuntimeError, Generic[T_ServiceType]):
    service_id: ServiceId[T_ServiceType]

    def __init__(self, service_id: ServiceId[T_ServiceType]) -> None:
        super().__init__(f"Service id not found: {service_id}")
        self.service_id = service_id
