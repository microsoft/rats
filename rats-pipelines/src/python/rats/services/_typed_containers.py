from abc import abstractmethod
from collections.abc import Iterable
from typing import Protocol

from ._service_managers import IProvideServices
from ._services import ServiceId, ServiceProvider, T_ServiceType, Tco_ServiceType


class IGetTypedServices(Protocol[Tco_ServiceType]):
    def get_service(self, service_name: str) -> Tco_ServiceType:
        return self.get_service_provider(service_name)()

    @abstractmethod
    def get_service_provider(self, service_name: str) -> ServiceProvider[Tco_ServiceType]: ...

    def get_service_group(self, group_name: str) -> Iterable[Tco_ServiceType]:
        for group in self.get_service_group_providers(group_name):
            yield group()

    @abstractmethod
    def get_service_group_providers(
        self,
        group_name: str,
    ) -> Iterable[ServiceProvider[Tco_ServiceType]]: ...


class TypedServiceContainer(IGetTypedServices[T_ServiceType]):
    _container: IProvideServices

    def __init__(self, container: IProvideServices) -> None:
        self._container = container

    def get_service_group_providers(
        self, group_name: str
    ) -> Iterable[ServiceProvider[T_ServiceType]]:
        return self._container.get_service_group_providers(ServiceId(group_name))

    def get_service_provider(self, service_name: str) -> ServiceProvider[T_ServiceType]:
        return lambda: self._container.get_service(ServiceId(service_name))
