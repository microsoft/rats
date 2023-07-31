from typing import Callable

from ._services import ServiceId, T_ServiceType


def service_provider(
    service_id: ServiceId[T_ServiceType],
) -> Callable[[Callable[..., T_ServiceType]], Callable[..., T_ServiceType]]:
    def wrapper(fn: Callable[..., T_ServiceType]) -> Callable[..., T_ServiceType]:
        setattr(fn, "__service_provider__", True)
        current = getattr(fn, "__service_ids__", [])
        current.append(service_id)
        setattr(fn, "__service_ids__", current)
        return fn

    return wrapper


def service_group(
    group_id: ServiceId[T_ServiceType],
) -> Callable[[Callable[..., T_ServiceType]], Callable[..., T_ServiceType]]:
    def wrapper(fn: Callable[..., T_ServiceType]) -> Callable[..., T_ServiceType]:
        setattr(fn, "__service_group_provider__", True)
        current = getattr(fn, "__service_group_ids__", [])
        current.append(group_id)
        setattr(fn, "__service_group_ids__", current)
        return fn

    return wrapper
