import logging
from abc import abstractmethod
from collections import defaultdict
from collections.abc import Callable, Iterable, Iterator, Mapping
from functools import cache
from importlib.metadata import entry_points
from typing import Any, NamedTuple, ParamSpec, Protocol, cast

from oneml.services import IExecutable, ServiceId, ServiceProvider, T_ServiceType

logger = logging.getLogger(__name__)
ANNOTATION_PROPERTY = "__habitat_service_ids__"
DEFAULT_CONTAINER_GROUP = "__containers__"
ExecutableLifecycle = Iterable[ServiceId[IExecutable]]


class ServiceCategory(NamedTuple):
    name: str


class AnnotatedFunction(Protocol):
    __habitat_service_ids__: Mapping[ServiceCategory, Mapping[str, Iterable[ServiceId[Any]]]]


class ServiceCategories:
    DEFAULT = ServiceCategory("default")
    GROUPS = ServiceCategory("groups")


# some replacements of old concepts
P = ParamSpec("P")


def service_provider(
    service_id: ServiceId[T_ServiceType],
) -> Callable[[Callable[P, T_ServiceType]], Callable[P, T_ServiceType]]:
    def wrapper(fn: Callable[P, T_ServiceType]) -> Callable[P, T_ServiceType]:
        attach_service_annotation(fn, service_id, ServiceCategories.DEFAULT)
        return fn

    return wrapper


def service_group(
    group_id: ServiceId[T_ServiceType],
) -> Callable[[Callable[..., T_ServiceType]], Callable[..., T_ServiceType]]:
    def wrapper(fn: Callable[..., T_ServiceType]) -> Callable[..., T_ServiceType]:
        attach_service_annotation(fn, group_id, ServiceCategories.GROUPS)
        return fn

    return wrapper


class ServiceContainer(Protocol):
    def get_service(self, service_id: ServiceId[T_ServiceType]) -> T_ServiceType:
        return self.get_service_provider(service_id)()

    def get_service_provider(
        self,
        service_id: ServiceId[T_ServiceType],
    ) -> ServiceProvider[T_ServiceType]:
        """Default here should be to parse public methods for annotated ids."""
        metadata = extract_service_annotations(type(self))[ServiceCategories.DEFAULT]
        group_metadata = extract_service_annotations(type(self))[ServiceCategories.GROUPS]
        container_group_id = ServiceId[ServiceContainer](DEFAULT_CONTAINER_GROUP)
        for method, service_ids in metadata.items():
            if service_id in service_ids:
                return getattr(self, method)
        for method, service_ids in group_metadata.items():
            if container_group_id in service_ids:
                sub_container = getattr(self, method)()
                try:
                    return sub_container.get_service_provider(service_id)
                except ValueError:
                    pass

        raise ValueError(f"Service {service_id} not found in {type(self)}")

    def get_service_group_provider(
        self,
        group_id: ServiceId[T_ServiceType],
    ) -> ServiceProvider[Iterable[T_ServiceType]]:
        """Default here should be to parse public methods for annotated ids."""
        return lambda: self.get_service_group(group_id)

    def get_service_group(self, group_id: ServiceId[T_ServiceType]) -> Iterable[T_ServiceType]:
        logger.debug(f"Searching for group: {group_id}")
        for group in self.get_service_group_providers(group_id):
            logger.debug(group_id)
            yield group()

    def get_service_group_providers(
        self,
        group_id: ServiceId[T_ServiceType],
    ) -> Iterable[ServiceProvider[T_ServiceType]]:
        """Default here should be to parse public methods for annotated ids."""
        metadata = extract_service_annotations(type(self))[ServiceCategories.GROUPS]
        container_group_id = ServiceId[ServiceContainer](DEFAULT_CONTAINER_GROUP)
        for method, service_ids in metadata.items():
            if group_id in service_ids:
                yield getattr(self, method)
            if container_group_id in service_ids:
                sub_container = getattr(self, method)()
                yield from sub_container.get_service_group_providers(group_id)


@cache
def extract_service_annotations(
    cls: object,
) -> Mapping[ServiceCategory, Mapping[str, Iterable[ServiceId[Any]]]]:
    results = defaultdict(lambda: defaultdict(list))
    for name in dir(cls):
        if name.startswith("_"):
            continue
        method = getattr(cls, name)
        if hasattr(method, ANNOTATION_PROPERTY):
            for category, service_ids in getattr(method, ANNOTATION_PROPERTY).items():
                results[category][name].extend(service_ids)

    return results


def attach_service_annotation(
    fn: Callable[P, T_ServiceType],
    service_id: ServiceId[T_ServiceType],
    category: ServiceCategory = ServiceCategories.DEFAULT,
) -> None:
    if not hasattr(fn, ANNOTATION_PROPERTY):
        fn.__habitat_service_ids__ = defaultdict(list)  # type: ignore[reportAssignmentType]

    # Should be safe to think of our function as annotated now
    logger.debug(f"attaching service {service_id} to {fn.__name__} in {category}")
    fn.__habitat_service_ids__[category].append(service_id)  # type: ignore[reportAssignmentType]


def container_group() -> Callable[[Callable[..., T_ServiceType]], Callable[..., T_ServiceType]]:
    return service_group(ServiceId[ServiceContainer](DEFAULT_CONTAINER_GROUP))


class App(IExecutable):
    _callback: Callable[[], None]

    def __init__(self, callback: Callable[[], None]) -> None:
        self._callback = callback

    def execute(self) -> None:
        self._callback()


class AppPlugin(Protocol):
    @abstractmethod
    def __call__(self, /, app: ServiceContainer) -> ServiceContainer:
        pass


class PluginServiceContainer(ServiceContainer):
    _app: ServiceContainer
    _group: str

    def __init__(self, app: ServiceContainer, group: str) -> None:
        self._app = app
        self._group = group

    def get_service_provider(
        self,
        service_id: ServiceId[T_ServiceType],
    ) -> ServiceProvider[T_ServiceType]:
        """Default here should be to parse public methods for annotated ids."""
        for sub in self._load_entry_points():
            try:
                return sub.get_service_provider(service_id)
            except ValueError:
                pass

        raise ValueError(f"Service {service_id} not found in {type(self)}")

    def get_service_group_providers(
        self,
        group_id: ServiceId[T_ServiceType],
    ) -> Iterable[ServiceProvider[T_ServiceType]]:
        """Default here should be to parse public methods for annotated ids."""
        for sub in self._load_entry_points():
            yield from sub.get_service_group_providers(group_id)

    @cache
    def _load_entry_points(self) -> Iterator[ServiceContainer]:
        entries = entry_points(group=self._group)
        if len(entries) == 0:
            return tuple()

        for entry in entries:
            plugin = cast(AppPlugin, entry.load())
            yield plugin(app=self._app)
