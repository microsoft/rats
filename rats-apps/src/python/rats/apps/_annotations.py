from collections.abc import Callable, Iterator
from typing import Any, Concatenate, Generic, NamedTuple, ParamSpec, TypeVar, cast

from rats import annotations

from ._ids import ServiceId, T_ServiceType
from ._namespaces import ProviderNamespaces
from ._scoping import scope_service_name

P = ParamSpec("P")
R = TypeVar("R")
T_Container = TypeVar("T_Container")


def service(
    service_id: ServiceId[T_ServiceType],
) -> Callable[[Callable[P, T_ServiceType]], Callable[P, T_ServiceType]]:
    """A service is anything you would create instances of?"""
    return annotations.annotation(ProviderNamespaces.SERVICES, cast(NamedTuple, service_id))


def autoid_service(fn: Callable[P, T_ServiceType]) -> Callable[P, T_ServiceType]:
    _service_id = autoid(fn)
    return annotations.annotation(ProviderNamespaces.SERVICES, cast(NamedTuple, _service_id))(fn)


def group(
    group_id: ServiceId[T_ServiceType],
) -> Callable[[Callable[P, Iterator[T_ServiceType]]], Callable[P, Iterator[T_ServiceType]]]:
    """A group is a collection of services."""
    return annotations.annotation(ProviderNamespaces.GROUPS, cast(NamedTuple, group_id))


def fallback_service(
    service_id: ServiceId[T_ServiceType],
) -> Callable[[Callable[P, T_ServiceType]], Callable[P, T_ServiceType]]:
    """A fallback service gets used if no service is defined."""
    return annotations.annotation(
        ProviderNamespaces.FALLBACK_SERVICES,
        cast(NamedTuple, service_id),
    )


def fallback_group(
    group_id: ServiceId[T_ServiceType],
) -> Callable[[Callable[P, Iterator[T_ServiceType]]], Callable[P, Iterator[T_ServiceType]]]:
    """A fallback group gets used if no group is defined."""
    return annotations.annotation(
        ProviderNamespaces.FALLBACK_GROUPS,
        cast(NamedTuple, group_id),
    )


def _factory_to_factory_provider(
    method: Callable[Concatenate[T_Container, P], R],
) -> Callable[[T_Container], Callable[P, R]]:
    """Convert a factory method a factory provider method returning the original method."""

    def new_method(self: T_Container) -> Callable[P, R]:
        def factory(*args: P.args, **kwargs: P.kwargs) -> R:
            return method(self, *args, **kwargs)

        return factory

    new_method.__name__ = method.__name__
    new_method.__module__ = method.__module__
    new_method.__qualname__ = method.__qualname__
    new_method.__doc__ = method.__doc__
    return new_method


class _FactoryService(Generic[P, R]):
    """
    A decorator to create a factory service.

    Decorate a method that takes any number of arguments and returns an object.  The resulting
    service will be that factory - taking the same arguments and returning a new object each time.
    """

    _service_id: ServiceId[Callable[P, R]]

    def __init__(self, service_id: ServiceId[Callable[P, R]]) -> None:
        self._service_id = service_id

    def __call__(
        self, method: Callable[Concatenate[T_Container, P], R]
    ) -> Callable[[T_Container], Callable[P, R]]:
        new_method = _factory_to_factory_provider(method)
        return service(self._service_id)(new_method)


# alias so we can think of it as a function
factory_service = _FactoryService


def autoid_factory_service(
    method: Callable[Concatenate[T_Container, P], R],
) -> Callable[[T_Container], Callable[P, R]]:
    """
    A decorator to create a factory service, with an automatically generated service id.

    Decorate a method that takes any number of arguments and returns an object.  The resulting
    service will be that factory - taking the same arguments and returning a new object each time.
    """
    new_method = _factory_to_factory_provider(method)
    return autoid_service(new_method)


def autoid(method: Callable[..., T_ServiceType]) -> ServiceId[T_ServiceType]:
    """
    Get a service id for a method.

    The service id is constructed from the module, class and method name.  It should be identical
    regardless of whether the method is bound or not, and regardless of the instance it is bound
    to.

    The service type is the return type of the method.
    """
    service_name = _get_method_service_id_name(method)
    return ServiceId[T_ServiceType](service_name)


def _get_method_service_id_name(method: Callable[..., Any]) -> str:
    tates = annotations.get_annotations(method).with_namespace(ProviderNamespaces.SERVICES)

    for a in tates.annotations:
        return a.groups[0].name

    module_name = method.__module__
    class_name, method_name = method.__qualname__.rsplit(".", 1)
    return scope_service_name(module_name, class_name, method_name)
