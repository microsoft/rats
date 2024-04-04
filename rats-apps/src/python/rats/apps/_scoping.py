from types import FunctionType
from typing import Any, ParamSpec, TypeVar, cast

from ._ids import ServiceId

T = TypeVar("T")
P = ParamSpec("P")


def autoscope(cls: type[T]) -> type[T]:
    """
    Decorator that replaces all ServiceId instances in the class with scoped ServiceId instances.

    The scoped ServiceId instances have a prefix to eliminate the chance of conflicts across
    packages.
    """
    def wrap(func: FunctionType) -> FunctionType:
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> FunctionType:
            result = func(*args, **kwargs)
            if not isinstance(result, ServiceId):
                return result

            return ServiceId[Any](f"{cls.__module__}:{cls.__name__}[{result.name}]")

        return cast(FunctionType, wrapper)

    props = [prop for prop in dir(cls) if not prop.startswith("_")]

    for prop_name in props:
        non_ns = getattr(cls, prop_name)

        if isinstance(non_ns, FunctionType):
            setattr(cls, prop_name, wrap(non_ns))
        else:
            if not isinstance(non_ns, ServiceId):
                continue

            prop = ServiceId[Any](f"{cls.__module__}:{cls.__name__}[{non_ns.name}]")
            setattr(cls, prop_name, prop)

    return cls
