from collections.abc import Callable
from typing import Any, ParamSpec

from rats import annotations

from ._ids import ConfigId, ServiceId, T_ConfigType, T_ServiceType
from ._namespaces import ProviderNamespaces
from ._scoping import scope_service_name

P = ParamSpec("P")


def service(
    service_id: ServiceId[T_ServiceType],
) -> Callable[[Callable[P, T_ServiceType]], Callable[P, T_ServiceType]]:
    """A service is anything you would create instances of?"""
    return annotations.annotation(ProviderNamespaces.SERVICES, service_id)


def autoid_service(fn: Callable[P, T_ServiceType]) -> Callable[P, T_ServiceType]:
    _service_id = autoid(fn)
    return annotations.annotation(ProviderNamespaces.SERVICES, _service_id)(fn)


def group(
    group_id: ServiceId[T_ServiceType],
) -> Callable[[Callable[P, T_ServiceType]], Callable[P, T_ServiceType]]:
    """A group is a collection of services."""
    return annotations.annotation(ProviderNamespaces.GROUPS, group_id)


def config(
    config_id: ConfigId[T_ConfigType],
) -> Callable[[Callable[P, T_ConfigType]], Callable[P, T_ConfigType]]:
    """A service that provides simple data-structures."""
    return annotations.annotation(
        ProviderNamespaces.SERVICES,
        config_id,
    )


def fallback_service(
    service_id: ServiceId[T_ServiceType],
) -> Callable[[Callable[P, T_ServiceType]], Callable[P, T_ServiceType]]:
    """A fallback service gets used if no service is defined."""
    return annotations.annotation(
        ProviderNamespaces.FALLBACK_SERVICES,
        service_id,
    )


def fallback_group(
    group_id: ServiceId[T_ServiceType],
) -> Callable[[Callable[P, T_ServiceType]], Callable[P, T_ServiceType]]:
    """A fallback group gets used if no group is defined."""
    return annotations.annotation(
        ProviderNamespaces.FALLBACK_GROUPS,
        group_id,
    )


def fallback_config(
    config_id: ConfigId[T_ConfigType],
) -> Callable[[Callable[P, T_ConfigType]], Callable[P, T_ConfigType]]:
    """A fallback config gets used if no config is defined."""
    return annotations.annotation(
        ProviderNamespaces.FALLBACK_SERVICES,
        config_id,
    )


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
