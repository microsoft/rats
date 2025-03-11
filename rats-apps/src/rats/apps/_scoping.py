from collections.abc import Callable
from types import FunctionType
from typing import Any, ParamSpec, TypeVar

from ._ids import ServiceId

T = TypeVar("T", bound=type)
P = ParamSpec("P")


def autoscope(cls: T) -> T:
    """Decorator to automatically scope ServiceId attributes in a class."""

    def _wrap(func: Callable[P, Any]) -> Callable[P, Any]:
        def _wrapper(*args: P.args, **kwargs: P.kwargs) -> ServiceId[Any]:
            result = func(*args, **kwargs)
            if not isinstance(result, ServiceId):
                return result

            return ServiceId[Any](scope_service_name(cls.__module__, cls.__name__, result.name))

        return _wrapper

    props = [prop for prop in dir(cls) if not prop.startswith("_")]

    for prop_name in props:
        non_ns = getattr(cls, prop_name)

        if isinstance(non_ns, FunctionType):
            setattr(cls, prop_name, _wrap(non_ns))
        else:
            if not isinstance(non_ns, ServiceId):
                continue

            prop = ServiceId[Any](scope_service_name(cls.__module__, cls.__name__, non_ns.name))
            setattr(cls, prop_name, prop)

    return cls


def scope_service_name(module_name: str, cls_name: str, name: str) -> str:
    """Generate a ServiceId name based on an objects module and class name."""
    return f"{module_name}:{cls_name}[{name}]"
