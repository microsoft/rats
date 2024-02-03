from collections.abc import Iterable, Mapping
from functools import lru_cache
from typing import Any, Protocol

from oneml.services import (
    DuplicateServiceIdError,
    IProvideServices,
    ServiceId,
    ServiceIdNotFoundError,
    ServiceProvider,
    T_ServiceType,
)


class DecoratedServiceProvider(IProvideServices, Protocol):

    def get_service_provider(
        self,
        service_id: ServiceId[T_ServiceType],
    ) -> ServiceProvider[T_ServiceType]:
        @lru_cache
        def parse_services() -> Mapping[ServiceId[Any], ServiceProvider[Any]]:
            result = {}
            methods = [attr for attr in dir(self) if not attr.startswith("_")]

            for method_name in methods:
                method = getattr(self, method_name)
                if getattr(method, "__service_provider__", False):
                    for sid in method.__service_ids__:
                        # some of this logic is duplicated/could be moved to some static functions
                        if sid in result:
                            raise DuplicateServiceIdError(sid)
                        result[sid] = method

            return result

        services = parse_services()
        if service_id not in services:
            raise ServiceIdNotFoundError(service_id)

        return services[service_id]

    def get_service_group_provider(
        self,
        group_id: ServiceId[T_ServiceType],
    ) -> ServiceProvider[Iterable[T_ServiceType]]:
        @lru_cache
        def parse_services() -> Mapping[ServiceId[Any], Iterable[ServiceProvider[Any]]]:
            result = {}
            methods = [attr for attr in dir(self) if not attr.startswith("_")]

            for method_name in methods:
                method = getattr(self, method_name)
                if getattr(method, "__service_group_ids__", False):
                    for sid in method.__service_group_ids__:
                        # some of this logic is duplicated/could be moved to some static functions
                        if sid not in result:
                            result[sid] = []

                        result[sid].append(method)

            return result

        group = parse_services()

        def gen() -> Iterable[T_ServiceType]:
            for p in group.get(group_id, tuple()):
                yield p()

        return gen

    def get_service_group_providers(
        self,
        group_id: ServiceId[T_ServiceType],
    ) -> Iterable[ServiceProvider[T_ServiceType]]:
        @lru_cache
        def parse_services() -> Mapping[ServiceId[Any], Iterable[ServiceProvider[Any]]]:
            result = {}
            methods = [attr for attr in dir(self) if not attr.startswith("_")]

            for method_name in methods:
                method = getattr(self, method_name)
                if getattr(method, "__service_group_ids__", False):
                    for sid in method.__service_group_ids__:
                        # some of this logic is duplicated/could be moved to some static functions
                        if sid not in result:
                            result[sid] = []

                        result[sid].append(method)

            return result

        group = parse_services()

        return group.get(group_id, tuple())
