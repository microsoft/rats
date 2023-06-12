from typing import Callable, Type, TypeVar, cast

from ._containers import ServiceProvider
from ._service_id import ServiceId

T = TypeVar("T")


def providers(*service_ids: ServiceId[T]) -> Callable[..., Callable[..., T]]:
    def decorator(func: Callable[..., T]) -> ServiceProvider[T]:
        setattr(func, "__service_provider__", True)
        current = getattr(func, "__service_ids__", [])
        current.extend(service_ids)
        setattr(func, "__service_ids__", current)

        return cast(ServiceProvider[T], func)

    return decorator


def provider(service_id: ServiceId[T]) -> Callable[..., Callable[..., T]]:
    def decorator(func: Callable[..., T]) -> ServiceProvider[T]:
        setattr(func, "__service_provider__", True)
        current = getattr(func, "__service_ids__", [])
        current.append(service_id)
        setattr(func, "__service_ids__", current)

        return cast(ServiceProvider[T], func)

    return decorator


def groups(*service_ids: ServiceId[T]) -> Callable[..., Callable[..., T]]:
    def decorator(func: Callable[..., T]) -> ServiceProvider[T]:
        setattr(func, "__service_group_provider__", True)
        current = getattr(func, "__service_group_ids__", [])
        current.extend(service_ids)
        setattr(func, "__service_group_ids__", current)

        return cast(ServiceProvider[T], func)

    return decorator


def group(service_id: ServiceId[T]) -> Callable[..., Callable[..., T]]:
    def decorator(func: Callable[..., T]) -> ServiceProvider[T]:
        setattr(func, "__service_group_provider__", True)
        current = getattr(func, "__service_group_ids__", [])
        current.append(service_id)
        setattr(func, "__service_group_ids__", current)

        return cast(ServiceProvider[T], func)

    return decorator


def scoped_service_ids(cls: Type[T]) -> Type[T]:
    """
    Decorator that replaces all ServiceId instances in the class with scoped ServiceId instances.

    The scoped ServiceId instances have a prefix to eliminate the chance of conflicts across
    packages.
    """
    props = [prop for prop in dir(cls) if prop.startswith('_') is False]

    for prop_name in props:
        non_ns = getattr(cls, prop_name)
        if not isinstance(non_ns, ServiceId):
            continue

        prop = ServiceId(
            f"{cls.__module__}.{cls.__name__}:{non_ns.name})",
        )
        setattr(cls, prop_name, prop)

    return cls
