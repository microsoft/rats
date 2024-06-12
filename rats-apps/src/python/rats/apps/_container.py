import abc
import warnings
from abc import abstractmethod
from collections.abc import Callable, Iterator
from typing import Generic, ParamSpec, Protocol

from ._annotations import extract_class_annotations, fn_annotation_decorator
from ._ids import ServiceId, T_ServiceType, Tco_ConfigType, Tco_ServiceType
from ._namespaces import ProviderNamespaces


class ServiceProvider(Protocol[Tco_ServiceType]):
    @abstractmethod
    def __call__(self) -> Tco_ServiceType:
        """Return the service instance."""


class ConfigProvider(ServiceProvider[Tco_ConfigType], Protocol[Tco_ConfigType]):
    @abstractmethod
    def __call__(self) -> Tco_ConfigType:
        """Return the config instance."""


class Container(Protocol):
    """Main interface for service containers."""

    def has(self, service_id: ServiceId[T_ServiceType]) -> bool:
        try:
            return self.get(service_id) is not None
        except ServiceNotFoundError:
            return False

    def has_group(self, group_id: ServiceId[T_ServiceType]) -> bool:
        try:
            return next(self.get_group(group_id)) is not None
        except StopIteration:
            return False

    def has_namespace(self, namespace: str, group_id: ServiceId[T_ServiceType]) -> bool:
        try:
            return next(self.get_namespaced_group(namespace, group_id)) is not None
        except StopIteration:
            return False

    def get(self, service_id: ServiceId[T_ServiceType]) -> T_ServiceType:
        """Retrieve a service instance by its id."""
        services = list(self.get_namespaced_group(ProviderNamespaces.SERVICES, service_id))
        if len(services) == 0:
            services.extend(
                list(self.get_namespaced_group(ProviderNamespaces.FALLBACK_SERVICES, service_id)),
            )

        if len(services) > 1:
            raise DuplicateServiceError(service_id)
        elif len(services) == 0:
            raise ServiceNotFoundError(service_id)
        else:
            return services[0]

    def get_group(
        self,
        group_id: ServiceId[T_ServiceType],
    ) -> Iterator[T_ServiceType]:
        """Retrieve a service group by its id."""
        if not self.has_namespace(ProviderNamespaces.GROUPS, group_id):
            yield from self.get_namespaced_group(ProviderNamespaces.FALLBACK_GROUPS, group_id)

        yield from self.get_namespaced_group(ProviderNamespaces.GROUPS, group_id)

    def get_namespaced_group(
        self,
        namespace: str,
        group_id: ServiceId[T_ServiceType],
    ) -> Iterator[T_ServiceType]:
        """Retrieve a service group by its id, within a given service namespace."""
        annotations = extract_class_annotations(type(self))
        containers = annotations.with_namespace(ProviderNamespaces.CONTAINERS)
        groups = annotations.group_in_namespace(namespace, group_id)

        for annotation in groups:
            yield getattr(self, annotation.name)()

        for container in containers:
            c = getattr(self, container.name)()
            yield from c.get_namespaced_group(namespace, group_id)


class AnnotatedContainer(Container, abc.ABC):
    def get_namespaced_group(
        self,
        namespace: str,
        group_id: ServiceId[T_ServiceType],
    ) -> Iterator[T_ServiceType]:
        warnings.warn(
            " ".join(
                [
                    "AnnotatedContainer.get_namespaced_group is deprecated and will be removed in the next major release.",
                    "AnnotatedContainer functionality has been moved into the apps.Container protocol.",
                    "Please extend apps.Container directly.",
                ]
            ),
            DeprecationWarning,
            stacklevel=2,
        )
        return super().get_namespaced_group(namespace, group_id)


DEFAULT_CONTAINER_GROUP = ServiceId[Container]("__default__")
P = ParamSpec("P")


def container(
    group_id: ServiceId[T_ServiceType] = DEFAULT_CONTAINER_GROUP,
) -> Callable[[Callable[P, T_ServiceType]], Callable[P, T_ServiceType]]:
    return fn_annotation_decorator(ProviderNamespaces.CONTAINERS, group_id)


class ServiceNotFoundError(RuntimeError, Generic[T_ServiceType]):
    service_id: ServiceId[T_ServiceType]

    def __init__(self, service_id: ServiceId[T_ServiceType]) -> None:
        super().__init__(f"Service id not found: {service_id}")
        self.service_id = service_id


class DuplicateServiceError(RuntimeError, Generic[T_ServiceType]):
    service_id: ServiceId[T_ServiceType]

    def __init__(self, service_id: ServiceId[T_ServiceType]) -> None:
        super().__init__(f"Service id provided multiple times: {service_id}")
        self.service_id = service_id
