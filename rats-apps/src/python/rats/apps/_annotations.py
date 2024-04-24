from collections import defaultdict
from collections.abc import Callable, Iterator
from functools import cache
from typing import Any, ParamSpec, cast

from typing_extensions import NamedTuple

from ._container import Container
from ._ids import ConfigId, ServiceId, T_ConfigType, T_ServiceType
from ._namespaces import ProviderNamespaces
from ._scoping import scope_service_name

DEFAULT_CONTAINER_GROUP = ServiceId[Container]("__default__")


class GroupAnnotations(NamedTuple):
    """
    The list of service ids attached to a given function.

    The `name` attribute is the name of the function, and the `namespace` attribute represents a
    specific meaning for the group of services.
    """

    name: str
    namespace: str
    groups: tuple[ServiceId[Any], ...]


class FunctionAnnotations(NamedTuple):
    """
    Holds metadata about the annotated service provider.

    Loosely inspired by: https://peps.python.org/pep-3107/.
    """

    providers: tuple[GroupAnnotations, ...]

    def group_in_namespace(
        self,
        namespace: str,
        group_id: ServiceId[T_ServiceType],
    ) -> tuple[GroupAnnotations, ...]:
        return tuple([x for x in self.with_namespace(namespace) if group_id in x.groups])

    def with_namespace(
        self,
        namespace: str,
    ) -> tuple[GroupAnnotations, ...]:
        return tuple([x for x in self.providers if x.namespace == namespace])


class FunctionAnnotationsBuilder:
    _service_ids: dict[str, list[ServiceId[Any]]]

    def __init__(self) -> None:
        self._service_ids = defaultdict(list)

    def add(self, namespace: str, service_id: ServiceId[T_ServiceType]) -> None:
        self._service_ids[namespace].append(service_id)

    def get_service_names(self, namespace: str) -> tuple[str, ...]:
        return tuple(s.name for s in self._service_ids.get(namespace, []))

    def make(self, name: str) -> tuple[GroupAnnotations, ...]:
        return tuple(
            [
                GroupAnnotations(name=name, namespace=namespace, groups=tuple(services))
                for namespace, services in self._service_ids.items()
            ]
        )


class AnnotatedContainer(Container):
    def get_namespaced_group(
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
            yield from c.get_namespaced_group(namespace, group_id)


P = ParamSpec("P")


def service(
    service_id: ServiceId[T_ServiceType],
) -> Callable[[Callable[P, T_ServiceType]], Callable[P, T_ServiceType]]:
    return fn_annotation_decorator(ProviderNamespaces.SERVICES, service_id)


def autoid_service(fn: Callable[P, T_ServiceType]) -> Callable[P, T_ServiceType]:
    _service_id = autoid(fn)
    _add_annotation(ProviderNamespaces.SERVICES, fn, _service_id)
    cached_fn = cache(fn)
    return cast(Callable[P, T_ServiceType], cached_fn)


def group(
    group_id: ServiceId[T_ServiceType],
) -> Callable[[Callable[P, T_ServiceType]], Callable[P, T_ServiceType]]:
    return fn_annotation_decorator(ProviderNamespaces.GROUPS, group_id)


def config(
    config_id: ConfigId[T_ConfigType],
) -> Callable[[Callable[P, T_ConfigType]], Callable[P, T_ConfigType]]:
    return fn_annotation_decorator(ProviderNamespaces.SERVICES, config_id)


def fallback_service(
    service_id: ServiceId[T_ServiceType],
) -> Callable[[Callable[P, T_ServiceType]], Callable[P, T_ServiceType]]:
    return fn_annotation_decorator(ProviderNamespaces.FALLBACK_SERVICES, service_id)


def fallback_group(
    group_id: ServiceId[T_ServiceType],
) -> Callable[[Callable[P, T_ServiceType]], Callable[P, T_ServiceType]]:
    return fn_annotation_decorator(ProviderNamespaces.FALLBACK_GROUPS, group_id)


def fallback_config(
    config_id: ConfigId[T_ConfigType],
) -> Callable[[Callable[P, T_ConfigType]], Callable[P, T_ConfigType]]:
    return fn_annotation_decorator(ProviderNamespaces.FALLBACK_SERVICES, config_id)


def container(
    group_id: ServiceId[T_ServiceType] = DEFAULT_CONTAINER_GROUP,
) -> Callable[[Callable[P, T_ServiceType]], Callable[P, T_ServiceType]]:
    return fn_annotation_decorator(ProviderNamespaces.CONTAINERS, group_id)


def _get_method_service_id_name(method: Callable[..., Any]) -> str:
    existing_names = _get_annotations_builder(method).get_service_names(
        ProviderNamespaces.SERVICES
    )
    if existing_names:
        return existing_names[0]
    else:
        module_name = method.__module__
        class_name, method_name = method.__qualname__.rsplit(".", 1)
        service_name = scope_service_name(module_name, class_name, method_name)
        return service_name


def autoid(method: Callable[..., T_ServiceType]) -> ServiceId[T_ServiceType]:
    """
    Get a service id for a method.

    The service id is constructed from the module, class and method name.  It should be identical
    regardless of whether the method is bound or not, and regardless of the instance it is bound
    to.

    The service type is the return type of the method.
    """
    service_name = _get_method_service_id_name(method)
    return ServiceId[T_ServiceType](service_name)


def fn_annotation_decorator(
    namespace: str,
    service_id: ServiceId[T_ServiceType],
) -> Callable[[Callable[P, T_ServiceType]], Callable[P, T_ServiceType]]:
    def wrapper(
        fn: Callable[P, T_ServiceType],
    ) -> Callable[P, T_ServiceType]:
        _service_id = service_id
        _add_annotation(namespace, fn, _service_id)
        cached_fn = cache(fn)
        # The static type of cached_fn should be correct, but it does not maintain the param-spec,
        # so we need to cast.
        return cast(Callable[P, T_ServiceType], cached_fn)

    return wrapper


@cache
def _extract_class_annotations(cls: Any) -> FunctionAnnotations:
    function_annotations: list[GroupAnnotations] = []
    for method_name in dir(cls):
        if method_name.startswith("_"):
            continue

        builder = _get_annotations_builder(getattr(cls, method_name))
        function_annotations.extend(list(builder.make(method_name)))

    return FunctionAnnotations(tuple(function_annotations))


def _add_annotation(namespace: str, fn: Any, service_id: ServiceId[T_ServiceType]) -> None:
    builder = _get_annotations_builder(fn)
    builder.add(namespace, service_id)


def _get_annotations_builder(fn: Any) -> FunctionAnnotationsBuilder:
    if not hasattr(fn, "__rats_service_annotations__"):
        fn.__rats_service_annotations__ = FunctionAnnotationsBuilder()

    return cast(FunctionAnnotationsBuilder, fn.__rats_service_annotations__)
