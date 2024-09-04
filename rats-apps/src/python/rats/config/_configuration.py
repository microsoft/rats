import functools
from collections.abc import Callable, Mapping, Sequence
from typing import Any, Generic, NamedTuple, ParamSpec, Protocol, TypeVar

from rats import annotations, apps

_CONFIGURATION_ANNOTATION_KEY = "__rats_config__"


class FactoryConfiguration(NamedTuple):
    service_id: apps.ServiceId[Callable[..., Any]]
    args: Sequence["Configuration"]
    kwargs: Mapping[str, "Configuration"]


Configuration = (
    int
    | str
    | float
    | bool
    | Sequence["Configuration"]
    | Mapping[str, "Configuration"]
    | FactoryConfiguration
)


class IObjectWithConfigurationAnnotation(Protocol):
    @property
    def __rats_config__(self) -> Configuration: ...


ConfiguredObject = (
    int
    | str
    | float
    | bool
    | Sequence["ConfiguredObject"]
    | Mapping[str, "ConfiguredObject"]
    | IObjectWithConfigurationAnnotation
)


def _get_configuration_from_annotation(obj: IObjectWithConfigurationAnnotation) -> Configuration:
    return getattr(obj, _CONFIGURATION_ANNOTATION_KEY)


def _set_configuration_as_annotation(
    obj: Any, configuration: Configuration
) -> IObjectWithConfigurationAnnotation:
    setattr(obj, _CONFIGURATION_ANNOTATION_KEY, configuration)
    return obj


class GetConfigurationFromObject:
    def _get_configuration_of_list(self, obj: Sequence[ConfiguredObject]) -> Configuration:
        return tuple(self(x) for x in obj)

    def _get_configuration_of_dict(self, obj: Mapping[str, ConfiguredObject]) -> Configuration:
        return {key: self(value) for key, value in obj.items()}

    def __call__(self, obj: ConfiguredObject) -> Configuration:
        if isinstance(obj, int):
            return obj
        elif isinstance(obj, str):
            return obj
        elif isinstance(obj, float):
            return obj
        elif isinstance(obj, bool):
            return obj
        elif isinstance(obj, Sequence):
            return self._get_configuration_of_list(obj)
        elif isinstance(obj, Mapping):
            return self._get_configuration_of_dict(obj)
        else:
            return _get_configuration_from_annotation(obj)


P = ParamSpec("P")
T_Container = TypeVar("T_Container", bound=apps.Container)
T = TypeVar("T")


def _get_service_id(
    method: Callable[[T_Container], Callable[P, T]],
) -> apps.ServiceId[Callable[P, T]]:
    tates = annotations.get_annotations(method)
    tates = tates.with_namespace(apps.ProviderNamespaces.SERVICES)
    service_ids: tuple[apps.ServiceId[Callable[P, T]]] = tuple(
        service_id for group in tates.annotations for service_id in group.groups
    )
    return service_ids[0]


def _factory_to_factory_with_config(
    method: Callable[[T_Container], Callable[P, T]],
) -> Callable[[T_Container], Callable[P, T]]:
    """
    Add configuration support to factory services.

    To be used as a decorator on a factory service provider method.

    A Factory service is a callable taking some arguments and returning an object.
    Adding support for configuration assumes the arguments are `ConfiguredObject` and ensures the
    returned object is a `ConfiguredObject`.

    Args:
        factory_provider: A method taking nothing and returning a factory service.

    Returns:
        A method wrapping over `factory_provider` and adding configuration support.
    """
    get_configuration_from_object = GetConfigurationFromObject()

    def _get_configuration_from_object(obj: Any) -> Configuration:
        return get_configuration_from_object(obj)

    @functools.wraps(method)
    def get_factory(container: T_Container) -> Callable[P, T]:
        service_id = _get_service_id(method)

        factory = method(container)

        def factory_with_config(*args: P.args, **kwargs: P.kwargs) -> T:
            configuration = FactoryConfiguration(
                service_id=service_id,
                args=tuple(_get_configuration_from_object(x) for x in args),
                kwargs={
                    key: _get_configuration_from_object(value) for key, value in kwargs.items()
                },
            )
            obj = factory(*args, **kwargs)
            _set_configuration_as_annotation(obj, configuration)
            return obj

        factory_with_config.__name__ = factory.__name__
        factory_with_config.__module__ = factory.__module__
        factory_with_config.__qualname__ = factory.__qualname__
        factory_with_config.__doc__ = factory.__doc__

        return factory_with_config

    return get_factory


class AssignConfigurationAsAnnotation:
    _get_configuration_from_annotation_service_id: apps.ServiceId[IGetConfigurationForObject]

    def __init__(
        self,
        get_configuration_from_annotation_service_id: apps.ServiceId[IGetConfigurationForObject],
    ) -> None:
        self._get_configuration_from_annotation_service_id = (
            get_configuration_from_annotation_service_id
        )

    def __call__(self, object: Any, configuration: Configuration) -> None:
        setattr(
            object,
            _GET_CONFIGURATION_FOR_OBJECT_SERVICE_ID_ANNOTATION_KEY,
            self._get_configuration_from_annotation_service_id,
        )
        setattr(object, _CONFIGURATION_ANNOTATION_KEY, configuration)


P = ParamSpec("P")
T = TypeVar("T")


class Factory(Generic[P, T]):
    _assign_configuration_as_annotation: AssignConfigurationAsAnnotation
    _self_service_id: apps.ServiceId[Callable[..., T]]
    _get_configuration_from_object: IGetConfigurationForObject
    _wrapped_factory: Callable[P, T]

    def __init__(
        self,
        assign_configuration_as_annotation: AssignConfigurationAsAnnotation,
        self_service_id: apps.ServiceId[Callable[..., T]],
        get_configuration_from_object: IGetConfigurationForObject,
        wrapped_factory: Callable[P, T],
    ) -> None:
        self._assign_configuration_as_annotation = assign_configuration_as_annotation
        self._self_service_id = self_service_id
        self._get_configuration_from_object = get_configuration_from_object
        self._wrapped_factory = wrapped_factory

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> T:
        obj = self._wrapped_factory(*args, **kwargs)
        configuration = FactoryConfiguration(
            service_id=self._self_service_id,
            args=[self._get_configuration_from_object(x) for x in args],
            kwargs={
                key: self._get_configuration_from_object(value) for key, value in kwargs.items()
            },
        )
        self._assign_configuration_as_annotation(obj, configuration)
        return obj


class ConfigurationToObject:
    _container: apps.Container

    def __init__(self, container: apps.Container) -> None:
        self._container = container

    def __call__(self, configuration: Configuration) -> Any:
        if isinstance(configuration, int):
            return configuration
        elif isinstance(configuration, str):
            return configuration
        elif isinstance(configuration, float):
            return configuration
        elif isinstance(configuration, bool):
            return configuration
        elif isinstance(configuration, list):
            return [self(x) for x in configuration]
        elif isinstance(configuration, dict):
            return {key: self(value) for key, value in configuration.items()}
        elif isinstance(configuration, FactoryConfiguration):
            service_id = configuration.service_id
            factory = self._container.get(service_id)
            args = [self(x) for x in configuration.args]
            kwargs = {key: self(value) for key, value in configuration.kwargs.items()}
            return factory(*args, **kwargs)
        else:
            raise ValueError(f"Unsupported configuration type: {type(configuration)}")
