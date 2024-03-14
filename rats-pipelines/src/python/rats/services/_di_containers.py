from collections.abc import Callable

from ._services import ServiceId, T_ServiceType


def service_provider(
    service_id: ServiceId[T_ServiceType],
) -> Callable[[Callable[..., T_ServiceType]], Callable[..., T_ServiceType]]:
    def wrapper(fn: Callable[..., T_ServiceType]) -> Callable[..., T_ServiceType]:
        fn.__service_provider__ = True  # type: ignore[attr-defined]
        current = getattr(fn, "__service_ids__", [])
        current.append(service_id)
        fn.__service_ids__ = current  # type: ignore[attr-defined]
        return fn

    return wrapper


def service_group(
    group_id: ServiceId[T_ServiceType],
) -> Callable[[Callable[..., T_ServiceType]], Callable[..., T_ServiceType]]:
    def wrapper(fn: Callable[..., T_ServiceType]) -> Callable[..., T_ServiceType]:
        fn.__service_group_provider__ = True  # type: ignore[attr-defined]
        current = getattr(fn, "__service_group_ids__", [])
        current.append(group_id)
        fn.__service_group_ids__ = current  # type: ignore[attr-defined]
        return fn

    return wrapper
