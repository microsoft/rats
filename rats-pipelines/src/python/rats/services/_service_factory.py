from collections.abc import Callable, Iterable
from typing import Any, cast

from ._executables import IExecutable
from ._service_managers import DuplicateServiceIdError, IManageServices, ServiceIdNotFoundError
from ._services import ServiceId, ServiceProvider, T_ServiceType


class ServiceFactory(IManageServices):
    """
    A service factory provides easy access to new instances of services.

    The expectation is that the factory will not cache multiple calls to `get_service()`. However,
    we make no effort to prevent the user from registering a provider that caches calls internally.
    """

    _providers: dict[ServiceId[Any], ServiceProvider[Any]]
    _groups: dict[ServiceId[Any], list[ServiceProvider[Any]]]

    def __init__(self) -> None:
        self._providers = {}
        self._groups = {}

    def get_callable_exe(self, exe_id: ServiceId[IExecutable]) -> Callable[[], None]:
        service = self.get_service_provider(exe_id)
        return lambda: service().execute()

    def get_service_provider(
        self, service_id: ServiceId[T_ServiceType]
    ) -> ServiceProvider[T_ServiceType]:
        if service_id not in self._providers:
            raise ServiceIdNotFoundError(service_id)

        # this lambda defers the checking of this key until the service is actually requested
        return lambda: self._providers[service_id]()

    def get_service_group_provider(
        self,
        group_id: ServiceId[T_ServiceType],
    ) -> ServiceProvider[Iterable[T_ServiceType]]:
        def gen() -> Iterable[T_ServiceType]:
            for p in self._groups.get(group_id, []):
                yield p()

        return gen

    def get_service_group_providers(
        self,
        group_id: ServiceId[T_ServiceType],
    ) -> Iterable[ServiceProvider[T_ServiceType]]:
        # We do not validate that the user gave us a group id that is the right type.
        return tuple(
            cast(Iterable[ServiceProvider[T_ServiceType]], self._groups.get(group_id, ())),
        )

    def add_service(
        self,
        service_id: ServiceId[T_ServiceType],
        provider: ServiceProvider[T_ServiceType],
    ) -> None:
        if service_id in self._providers:
            raise DuplicateServiceIdError[T_ServiceType](service_id)

        self._providers[service_id] = provider

    def add_group(
        self,
        group_id: ServiceId[T_ServiceType],
        provider: ServiceProvider[T_ServiceType],
    ) -> None:
        group = self._groups.get(group_id, [])
        group.append(provider)
        self._groups[group_id] = group
