import abc
import logging
from abc import abstractmethod
from collections.abc import Callable, Iterator
from typing import Generic, ParamSpec, Protocol

from typing_extensions import deprecated

from rats import annotations

from ._ids import ServiceId, T_ServiceType, Tco_ConfigType, Tco_ServiceType
from ._namespaces import ProviderNamespaces

logger = logging.getLogger(__name__)


class ServiceProvider(Protocol[Tco_ServiceType]):
    @abstractmethod
    def __call__(self) -> Tco_ServiceType:
        """Return the service instance."""


class ConfigProvider(ServiceProvider[Tco_ConfigType], Protocol[Tco_ConfigType]):
    @abstractmethod
    def __call__(self) -> Tco_ConfigType:
        """Return the config instance."""


class Container(Protocol):
    """
    Main interface for service containers.

    The default methods in this protocol  attempt to find service providers that have been
    annotated.

    Example:
        .. code-block:: python

            from rats import apps


            class MyStorageClient:
                def save(self, data: str) -> None:
                    print(f"Saving data: {data}")


            class MyPluginServices:
                STORAGE_CLIENT = ServiceId[MyStorageClient]("storage-client")


            class MyPluginContainer(apps.Container):
                @apps.service(MyPluginServices.STORAGE_CLIENT)
                def _storage_client() -> MyStorageClient:
                    return MyStorageClient()


            container = MyPluginContainer()
            storage_client = container.get(MyPluginServices.STORAGE_CLIENT)
            storage_client.save("Hello, world!")
    """

    def has(self, service_id: ServiceId[T_ServiceType]) -> bool:
        """
        Check if a service is provided by this container.

        Example:
            .. code-block:: python

                if not container.has(MyPluginServices.STORAGE_CLIENT):
                    print("Did you forget to configure a storage client?")
        """
        try:
            return self.get(service_id) is not None
        except ServiceNotFoundError:
            return False

    def has_group(self, group_id: ServiceId[T_ServiceType]) -> bool:
        """Check if a service group has at least one provider in the container."""
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
        tates = annotations.get_class_annotations(type(self))
        containers = tates.with_namespace(ProviderNamespaces.CONTAINERS)
        groups = tates.with_group(namespace, group_id)

        for annotation in groups.annotations:
            if not hasattr(self, f"__rats_cache_{annotation.name}"):
                setattr(self, f"__rats_cache_{annotation.name}", getattr(self, annotation.name)())

            yield getattr(self, f"__rats_cache_{annotation.name}")

        for annotation in containers.annotations:
            if not hasattr(self, f"__rats_container_cache_{annotation.name}"):
                setattr(
                    self,
                    f"__rats_container_cache_{annotation.name}",
                    getattr(self, annotation.name)(),
                )

            c = getattr(self, f"__rats_container_cache_{annotation.name}")
            yield from c.get_namespaced_group(namespace, group_id)


@deprecated(
    " ".join(
        [
            "AnnotatedContainer is deprecated and will be removed in the next major release.",
            "The functionality has been moved into the apps.Container protocol.",
            "Please extend apps.Container directly.",
        ]
    ),
    stacklevel=2,
)
class AnnotatedContainer(Container, abc.ABC):
    """
    A Container implementation that extracts providers from its annotated methods.

    .. deprecated:: 0.1.3
    The behavior of this class has been made the default within ``Container``.
    """


DEFAULT_CONTAINER_GROUP = ServiceId[Container]("__default__")
P = ParamSpec("P")


def container(
    group_id: ServiceId[T_ServiceType] = DEFAULT_CONTAINER_GROUP,
) -> Callable[[Callable[P, T_ServiceType]], Callable[P, T_ServiceType]]:
    return annotations.annotation(ProviderNamespaces.CONTAINERS, group_id)


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
