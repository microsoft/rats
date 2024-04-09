from collections import defaultdict
from collections.abc import Callable, Iterator
from functools import cache
from typing import Any, cast

from typing_extensions import NamedTuple

from ._container import Container
from ._ids import ConfigId, ServiceId, T_ConfigType, T_ServiceType
from ._namespaces import ProviderNamespaces

DEFAULT_CONTAINER_GROUP = ServiceId[Container]("__default__")


class ProviderAnnotationsNamespace(NamedTuple):
    """
    The list of service ids attached to a given function.

    The `name` attribute is the name of the function, and the `namespace` attribute represents a
    specific meaning for the group of services.
    """
    name: str
    namespace: str
    group: tuple[ServiceId[Any], ...]


class ServiceAnnotations(NamedTuple):
    """
    Holds metadata about the annotated service provider.

    Loosely inspired by: https://peps.python.org/pep-3107/.
    """
    providers: tuple[ProviderAnnotationsNamespace, ...]

    def group_in_namespace(
        self,
        namespace: str,
        group_id: ServiceId[T_ServiceType],
    ) -> tuple[ProviderAnnotationsNamespace, ...]:
        return tuple([x for x in self.with_namespace(namespace) if group_id in x.group])

    def with_namespace(
        self,
        namespace: str,
    ) -> tuple[ProviderAnnotationsNamespace, ...]:
        return tuple([x for x in self.providers if x.namespace == namespace])


class FunctionAnnotationsBuilder:
    _service_ids: dict[str, list[ServiceId[Any]]]

    def __init__(self) -> None:
        self._service_ids = defaultdict(list)

    def add(self, namespace: str, service_id: ServiceId[T_ServiceType]) -> None:
        self._service_ids[namespace].append(service_id)

    def make(self, name: str) -> tuple[ProviderAnnotationsNamespace, ...]:
        return tuple(
            [
                ProviderAnnotationsNamespace(name=name, namespace=namespace, group=tuple(services))
                for namespace, services in self._service_ids.items()
            ]
        )


class AnnotatedContainer(Container):

    def get_namespace(
        self,
        namespace: str,
        group_id: ServiceId[T_ServiceType],
    ) -> Iterator[T_ServiceType]:
        annotations = _extract_class_annotations(type(self))
        containers = annotations.with_namespace(ProviderNamespaces.CONTAINERS)
        groups = annotations.group_in_namespace(namespace, group_id)

        for annotation in groups:
            yield getattr(self, annotation.name)()

        for container in containers:
            c = getattr(self, container.name)()
            yield from c.get_namespace(namespace, group_id)


def service(
    service_id: ServiceId[T_ServiceType],
) -> Callable[..., Callable[..., T_ServiceType]]:
    return fn_annotation_decorator(ProviderNamespaces.SERVICES, service_id)


def group(
    group_id: ServiceId[T_ServiceType],
) -> Callable[..., Callable[..., T_ServiceType]]:
    return fn_annotation_decorator(ProviderNamespaces.GROUPS, group_id)


def config(
    config_id: ConfigId[T_ConfigType],
) -> Callable[..., Callable[..., T_ConfigType]]:
    return fn_annotation_decorator(ProviderNamespaces.CONFIGS, config_id)


def fallback_service(
    service_id: ServiceId[T_ServiceType],
) -> Callable[..., Callable[..., T_ServiceType]]:
    return fn_annotation_decorator(ProviderNamespaces.FALLBACK_SERVICES, service_id)


def fallback_group(
    group_id: ServiceId[T_ServiceType],
) -> Callable[..., Callable[..., T_ServiceType]]:
    return fn_annotation_decorator(ProviderNamespaces.FALLBACK_GROUPS, group_id)


def fallback_config(
    config_id: ConfigId[T_ConfigType],
) -> Callable[..., Callable[..., T_ConfigType]]:
    return fn_annotation_decorator(ProviderNamespaces.FALLBACK_CONFIGS, config_id)


def container(
    group_id: ServiceId[T_ServiceType] = DEFAULT_CONTAINER_GROUP,
) -> Callable[..., Callable[..., T_ServiceType]]:
    return fn_annotation_decorator(ProviderNamespaces.CONTAINERS, group_id)


def fn_annotation_decorator(
    namespace: str,
    service_id: ServiceId[T_ServiceType],
) -> Callable[..., Callable[..., T_ServiceType]]:
    def wrapper(
        fn: Callable[..., T_ServiceType],
    ) -> Callable[..., T_ServiceType]:
        _add_annotation(namespace, fn, service_id)
        return cache(fn)

    return wrapper


@cache
def _extract_class_annotations(cls: Any) -> ServiceAnnotations:
    function_annotations: list[ProviderAnnotationsNamespace] = []
    for method_name in dir(cls):
        if method_name.startswith("_"):
            continue

        builder = _get_annotations_builder(getattr(cls, method_name))
        function_annotations.extend(list(builder.make(method_name)))

    return ServiceAnnotations(tuple(function_annotations))


def _add_annotation(namespace: str, fn: Any, service_id: ServiceId[T_ServiceType]) -> None:
    builder = _get_annotations_builder(fn)
    builder.add(namespace, service_id)


def _get_annotations_builder(fn: Any) -> FunctionAnnotationsBuilder:
    if not hasattr(fn, "__rats_service_annotations__"):
        fn.__rats_service_annotations__ = FunctionAnnotationsBuilder()

    return cast(FunctionAnnotationsBuilder, fn.__rats_service_annotations__)
