from collections.abc import Callable
from typing import NamedTuple, ParamSpec, TypeVar
from rats import annotations


class ProviderNamespaces:
    CONFIGURED_OBJECT_FACTORIES = "configured-object-factories"


class ConfiguredObjectFactoryId(NamedTuple):
    name: str = "configured-object-factory"


P = ParamSpec("P")
T = TypeVar("T")


def configured_object_factory(fn: Callable[P, T]) -> Callable[P, T]:
    annotator = annotations.annotation(
        ProviderNamespaces.CONFIGURED_OBJECT_FACTORIES, ConfiguredObjectFactoryId()
    )
    return annotator(fn)


def find_configured_object_factory_methods_in_class(cls: type) -> tuple[str, ...]:
    tates = annotations.get_class_annotations(cls)
    tates.with_group(ProviderNamespaces.CONFIGURED_OBJECT_FACTORIES, ConfiguredObjectFactoryId())
    anns = tates.annotations
    method_names = tuple(ann.name for ann in anns)
    return method_names
