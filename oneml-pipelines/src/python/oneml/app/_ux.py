from typing import Callable, Type, TypeVar

from oneml.services import IExecutable, ServiceId

T = TypeVar("T")


def scoped_pipeline_ids(cls: Type[T]) -> Type[T]:
    """
    Decorator that replaces all ServiceId instances in the class with scoped ServiceId instances.

    The scoped ServiceId instances have a prefix to eliminate the chance of conflicts across
    packages.
    """
    props = [prop for prop in dir(cls) if prop.startswith("_") is False]

    for prop_name in props:
        non_ns = getattr(cls, prop_name)
        if not isinstance(non_ns, ServiceId):
            continue

        prop = ServiceId(
            f"{cls.__module__}.{cls.__name__}:{non_ns.name}[pipeline]",
        )
        setattr(cls, prop_name, prop)

    return cls


def pipeline(service_id: ServiceId[IExecutable]) -> Callable[..., Callable[..., None]]:
    def decorator(func: Callable[..., None]) -> Callable[..., None]:
        setattr(func, "__executable__", True)
        current = getattr(func, "__executable_ids__", [])
        current.append(service_id)
        setattr(func, "__executable_ids__", current)

        return func

    return decorator