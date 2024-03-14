from collections.abc import Callable
from typing import Any, TypeVar

from rats.services import IExecutable, ServiceId

T = TypeVar("T")


def scoped_pipeline_ids(cls: type[T]) -> type[T]:
    """
    Decorator that replaces all ServiceId instances in the class with scoped ServiceId instances.

    The scoped ServiceId instances have a prefix to eliminate the chance of conflicts across
    packages.
    """
    props: list[str] = [prop for prop in dir(cls) if prop.startswith("_") is False]

    for prop_name in props:
        non_ns = getattr(cls, prop_name)
        if not isinstance(non_ns, ServiceId):
            continue

        prop = ServiceId[Any](
            f"{cls.__module__}.{cls.__name__}:{non_ns.name}[pipeline]",
        )
        setattr(cls, prop_name, prop)

    return cls


def pipeline(service_id: ServiceId[IExecutable]) -> Callable[..., Callable[..., None]]:
    def decorator(func: Callable[..., None]) -> Callable[..., None]:
        func.__executable__ = True  # type: ignore[attr-defined]
        current = getattr(func, "__executable_ids__", [])
        current.append(service_id)
        func.__executable_ids__ = current  # type: ignore[attr-defined]

        return func

    return decorator
