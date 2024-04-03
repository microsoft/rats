from collections import defaultdict
from collections.abc import Callable, Iterator
from functools import cache
from typing import Any, Generic, cast

from typing_extensions import NamedTuple

from ._categories import ProviderCategories
from ._container import Container
from ._ids import ConfigId, P_ProviderParams, ServiceId, T_ConfigType, T_ServiceType


class FunctionAnnotations(NamedTuple, Generic[T_ServiceType]):
    name: str
    category_id: ServiceId[T_ServiceType]
    values: tuple[ServiceId[T_ServiceType]]


class ClassAnnotations(NamedTuple):
    values: tuple[FunctionAnnotations, ...]

    def find_in_category(
        self,
        category_id: ServiceId[T_ServiceType],
        group_id: ServiceId[T_ServiceType],
    ) -> tuple[FunctionAnnotations[T_ServiceType], ...]:
        return tuple([x for x in self.with_category(category_id) if group_id in x.values])

    def with_category(
        self,
        category_id: ServiceId[T_ServiceType],
    ) -> tuple[FunctionAnnotations[T_ServiceType], ...]:
        return tuple([x for x in self.values if x.category_id == category_id])


class FunctionAnnotationsBuilder:
    _service_ids: dict[ServiceId[Any], list[ServiceId[Any]]]

    def __init__(self) -> None:
        self._service_ids = defaultdict(list)

    def add(self, category_id: ServiceId[T_ServiceType], service_id: ServiceId[T_ServiceType]) -> None:
        self._service_ids[category_id].append(service_id)

    def make(self, name: str) -> tuple[FunctionAnnotations, ...]:
        return tuple(
            [
                FunctionAnnotations[Any](name=name, category_id=category_id, values=tuple(services))
                for category_id, services in self._service_ids.items()
            ]
        )


class AnnotatedContainer(Container):

    def get_category(
        self,
        category_id: ServiceId[T_ServiceType],
        group_id: ServiceId[T_ServiceType],
    ) -> Iterator[T_ServiceType]:
        annotations = _extract_class_annotations(type(self))
        containers = annotations.with_category(ProviderCategories.CONTAINER)
        groups = annotations.find_in_category(category_id, group_id)

        for annotation in groups:
            yield getattr(self, annotation.name)()

        for container in containers:
            c = getattr(self, container.name)()
            yield from c.get_category(category_id, group_id)


def service(
    service_id: ServiceId[T_ServiceType],
) -> Callable[[Callable[P_ProviderParams, T_ServiceType]], Callable[P_ProviderParams, T_ServiceType]]:
    return fn_annotation_decorator(ProviderCategories.SERVICE, service_id)


def group(
    group_id: ServiceId[T_ServiceType],
) -> Callable[[Callable[P_ProviderParams, T_ServiceType]], Callable[P_ProviderParams, T_ServiceType]]:
    return fn_annotation_decorator(ProviderCategories.GROUP, group_id)


def config(
    config_id: ConfigId[T_ConfigType],
) -> Callable[[Callable[P_ProviderParams, T_ConfigType]], Callable[P_ProviderParams, T_ConfigType]]:
    return fn_annotation_decorator(ProviderCategories.CONFIG, config_id)


def fallback_service(
    service_id: ServiceId[T_ServiceType],
) -> Callable[[Callable[P_ProviderParams, T_ServiceType]], Callable[P_ProviderParams, T_ServiceType]]:
    return fn_annotation_decorator(ProviderCategories.FALLBACK_SERVICE, service_id)


def fallback_group(
    group_id: ServiceId[T_ServiceType],
) -> Callable[[Callable[P_ProviderParams, T_ServiceType]], Callable[P_ProviderParams, T_ServiceType]]:
    return fn_annotation_decorator(ProviderCategories.FALLBACK_GROUP, group_id)


def fallback_config(
    config_id: ConfigId[T_ConfigType],
) -> Callable[[Callable[P_ProviderParams, T_ConfigType]], Callable[P_ProviderParams, T_ConfigType]]:
    return fn_annotation_decorator(ProviderCategories.FALLBACK_CONFIG, config_id)


def container(
    group_id: ServiceId[T_ServiceType] = ServiceId[Container]("__default__"),
) -> Callable[[Callable[P_ProviderParams, T_ServiceType]], Callable[P_ProviderParams, T_ServiceType]]:
    return fn_annotation_decorator(ProviderCategories.CONTAINER, group_id)


def fn_annotation_decorator(
    category_id: ServiceId[T_ServiceType],
    service_id: ServiceId[T_ServiceType],
) -> Callable[P_ProviderParams, T_ServiceType]:
    def wrapper(
        fn: Callable[P_ProviderParams, T_ServiceType],
    ) -> Callable[P_ProviderParams, T_ServiceType]:
        _add_annotation(category_id, fn, service_id)
        return cache(fn)

    return wrapper


@cache
def _extract_class_annotations(cls: Any) -> ClassAnnotations:
    function_annotations = []
    for method_name in dir(cls):
        if method_name.startswith("_"):
            continue

        builder = _get_annotations_builder(getattr(cls, method_name))
        function_annotations.extend(builder.make(method_name))

    return ClassAnnotations(tuple(function_annotations))


def _add_annotation(category_id: ServiceId[T_ServiceType], fn: Any, service_id: ServiceId[T_ServiceType]) -> None:
    builder = _get_annotations_builder(fn)
    builder.add(category_id, service_id)


def _get_annotations_builder(fn: Any) -> FunctionAnnotationsBuilder:
    if not hasattr(fn, "__rats_service_annotations__"):
        fn.__rats_service_annotations__ = FunctionAnnotationsBuilder()

    return cast(FunctionAnnotationsBuilder, fn.__rats_service_annotations__)
