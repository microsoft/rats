from types import FunctionType
from typing import Any, TypeVar, cast

from ._contexts import ContextId
from ._services import ServiceId

T = TypeVar("T")


def scoped_service_ids(cls: type[T]) -> type[T]:
    """
    Decorator that replaces all ServiceId instances in the class with scoped ServiceId instances.

    The scoped ServiceId instances have a prefix to eliminate the chance of conflicts across
    packages.
    """

    def wrap(func: FunctionType) -> FunctionType:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            result = func(*args, **kwargs)
            if not isinstance(result, ServiceId):
                return result

            return ServiceId(f"{cls.__module__}.{cls.__name__}:{result.name}")

        return cast(FunctionType, wrapper)

    props = [prop for prop in dir(cls) if prop.startswith("_") is False]

    for prop_name in props:
        non_ns = getattr(cls, prop_name)

        if isinstance(non_ns, FunctionType):
            setattr(cls, prop_name, wrap(non_ns))
        else:
            if not isinstance(non_ns, ServiceId):
                continue

            prop = ServiceId[Any](f"{cls.__module__}.{cls.__name__}:{non_ns.name}")
            setattr(cls, prop_name, prop)

    return cls


def scoped_context_ids(cls: type[T]) -> type[T]:
    """
    Decorator that replaces all ContextId instances in the class with scoped ContextId instances.

    The scoped ContextId instances have a prefix to eliminate the chance of conflicts across
    packages.
    """

    def wrap(func: FunctionType) -> FunctionType:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            result = func(*args, **kwargs)
            if not isinstance(result, ContextId):
                return result

            return ContextId(f"{cls.__module__}.{cls.__name__}:{result.name}")

        return cast(FunctionType, wrapper)

    props = [prop for prop in dir(cls) if prop.startswith("_") is False]

    for prop_name in props:
        non_ns = getattr(cls, prop_name)

        if isinstance(non_ns, FunctionType):
            setattr(cls, prop_name, wrap(non_ns))
        else:
            if not isinstance(non_ns, ContextId):
                continue

            prop = ContextId[Any](f"{cls.__module__}.{cls.__name__}:{non_ns.name}")
            setattr(cls, prop_name, prop)

    return cls
