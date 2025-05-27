import logging
from abc import abstractmethod
from collections.abc import Callable, Iterator
from typing import Any, Generic, NamedTuple, ParamSpec, Protocol, cast

from typing_extensions import NamedTuple as ExtNamedTuple

from rats import annotations

from ._ids import ServiceId, T_ServiceType, Tco_ServiceType
from ._namespaces import ProviderNamespaces

logger = logging.getLogger(__name__)


class Provider(Protocol[Tco_ServiceType]):
    @abstractmethod
    def __call__(self) -> Tco_ServiceType:
        """Return the service instance."""


class GroupProvider(Protocol[Tco_ServiceType]):
    @abstractmethod
    def __call__(self) -> Iterator[Tco_ServiceType]:
        """Return the group instances."""


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
            # groups are expected to return iterable services
            for i in self.get_namespaced_group(ProviderNamespaces.FALLBACK_GROUPS, group_id):
                yield from cast(Iterator[T_ServiceType], i)

        for i in self.get_namespaced_group(ProviderNamespaces.GROUPS, group_id):
            yield from cast(Iterator[T_ServiceType], i)

    def get_namespaced_group(
        self,
        namespace: str,
        group_id: ServiceId[T_ServiceType],
    ) -> Iterator[T_ServiceType]:
        """Retrieve a service group by its id, within a given service namespace."""
        yield from _get_cached_services_for_group(self, namespace, group_id)

        for subcontainer in _get_subcontainers(self):
            yield from subcontainer.get_namespaced_group(namespace, group_id)


def _get_subcontainers(c: Container) -> Iterator[Container]:
    yield from _get_cached_services_for_group(
        c, ProviderNamespaces.CONTAINERS, DEFAULT_CONTAINER_GROUP
    )


class _ProviderInfo(ExtNamedTuple, Generic[T_ServiceType]):
    attr: str
    group_id: ServiceId[T_ServiceType]


def _get_cached_services_for_group(
    c: Container,
    namespace: str,
    group_id: ServiceId[T_ServiceType],
) -> Iterator[T_ServiceType]:
    provider_cache = _get_provider_cache(c)
    info_cache = _get_provider_info_cache(c)

    if (namespace, group_id) not in info_cache:
        info_cache[(namespace, group_id)] = list(_get_providers_for_group(c, namespace, group_id))

    for provider in info_cache[(namespace, group_id)]:
        if provider not in provider_cache:
            if namespace in [
                ProviderNamespaces.CONTAINERS,
                ProviderNamespaces.SERVICES,
                ProviderNamespaces.FALLBACK_SERVICES,
            ]:
                provider_cache[provider] = getattr(c, provider.attr)()
            else:
                provider_cache[provider] = list(getattr(c, provider.attr)())

        yield provider_cache[provider]


def _get_provider_cache(obj: object) -> dict[_ProviderInfo[Any], Any]:
    if not hasattr(obj, "__rats_apps_provider_cache__"):
        obj.__rats_apps_provider_cache__ = {}  # type: ignore[reportAttributeAccessIssue]

    return obj.__rats_apps_provider_cache__  # type: ignore[reportAttributeAccessIssue]


def _get_provider_info_cache(
    obj: object,
) -> dict[tuple[str, ServiceId[Any]], list[_ProviderInfo[Any]]]:
    if not hasattr(obj, "__rats_apps_provider_info_cache__"):
        obj.__rats_apps_provider_info_cache__ = {}  # type: ignore[reportAttributeAccessIssue]

    return obj.__rats_apps_provider_info_cache__  # type: ignore[reportAttributeAccessIssue]


def _get_providers_for_group(
    c: Container,
    namespace: str,
    group_id: ServiceId[T_ServiceType],
) -> Iterator[_ProviderInfo[T_ServiceType]]:
    tates = annotations.get_class_annotations(type(c))
    groups = tates.with_group(namespace, cast(NamedTuple, group_id))

    for annotation in groups.annotations:
        yield _ProviderInfo(annotation.name, group_id)


DEFAULT_CONTAINER_GROUP = ServiceId[Container](f"{__name__}:__default__")
P = ParamSpec("P")


def container(
    group_id: ServiceId[T_ServiceType] = DEFAULT_CONTAINER_GROUP,
) -> Callable[[Callable[P, T_ServiceType]], Callable[P, T_ServiceType]]:
    return annotations.annotation(ProviderNamespaces.CONTAINERS, cast(NamedTuple, group_id))


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
