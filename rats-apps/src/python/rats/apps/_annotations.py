from collections.abc import Callable
from typing import Any

from rats import annotations

from ._ids import ServiceId, T_ServiceType
from ._namespaces import ProviderNamespaces
from ._scoping import scope_service_name


def service(service_id: ServiceId[T_ServiceType]) -> annotations.DecoratorType:
    """A service is anything you would create instances of?"""
    return annotations.annotation(ProviderNamespaces.SERVICES, service_id)


def autoid_service(fn: annotations.FunctionType) -> annotations.FunctionType:
    _service_id = autoid(fn)
    return annotations.annotation(ProviderNamespaces.SERVICES, _service_id)(fn)


def group(group_id: ServiceId[T_ServiceType]) -> annotations.DecoratorType:
    """A group is a collection of services."""
    return annotations.annotation(ProviderNamespaces.GROUPS, group_id)


def fallback_service(
    service_id: ServiceId[T_ServiceType],
) -> annotations.DecoratorType:
    """A fallback service gets used if no service is defined."""
    return annotations.annotation(ProviderNamespaces.FALLBACK_SERVICES, service_id)


def fallback_group(
    group_id: ServiceId[T_ServiceType],
) -> annotations.DecoratorType:
    """A fallback group gets used if no group is defined."""
    return annotations.annotation(ProviderNamespaces.FALLBACK_GROUPS, group_id)


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
