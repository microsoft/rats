from ast import Call
import functools
from collections.abc import Callable, Mapping, Sequence
from typing import Any, Generic, NamedTuple, ParamSpec, Protocol, TypeVar

from rats import annotations, apps
from ._annotations import ProviderNamespaces


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


class FactoryToFactoryWithConfig:
    _get_configuration_from_object: GetConfigurationFromObject

    def __init__(self, get_configuration_from_object: GetConfigurationFromObject) -> None:
        self._get_configuration_from_object = get_configuration_from_object

    def _cast_as_configured_object(self, obj: Any) -> ConfiguredObject:
        return obj

    def _get_configuration(self, obj: Any) -> Configuration:
        return self._get_configuration_from_object(self._cast_as_configured_object(obj))

    def _get_args_configuration(self, args: Sequence[Any]) -> Sequence[Configuration]:
        return tuple(self._get_configuration(x) for x in args)

    def _get_kwargs_configuration(self, kwargs: Mapping[str, Any]) -> Mapping[str, Configuration]:
        return {key: self._get_configuration(value) for key, value in kwargs.items()}

    def __call__(
        self, service_id: apps.ServiceId[Callable[P, T]], factory: Callable[P, T]
    ) -> Callable[P, T]:
        @functools.wraps(factory)
        def factory_with_config(*args: P.args, **kwargs: P.kwargs) -> T:
            args_configuration = self._get_args_configuration(args)
            kwargs_configuration = self._get_kwargs_configuration(kwargs)
            configuration = FactoryConfiguration(
                service_id=service_id,
                args=args_configuration,
                kwargs=kwargs_configuration,
            )
            obj = factory(*args, **kwargs)
            _set_configuration_as_annotation(obj, configuration)
            return obj

        return factory_with_config


class FactoryProviderToFactoryWithConfigProvider:
    _factory_to_factory_with_config: FactoryToFactoryWithConfig

    def __init__(self, factory_to_factory_with_config: FactoryToFactoryWithConfig) -> None:
        self._factory_to_factory_with_config = factory_to_factory_with_config

    def __call__(
        self, factory_provider: Callable[[T_Container], Callable[P, T]]
    ) -> Callable[[T_Container], Callable[P, T]]:
        service_id = apps.get_method_service_id(factory_provider)

        @annotations.wraps(factory_provider)
        def factory_with_config_provider(container: T_Container) -> Callable[P, T]:
            factory = factory_provider(container)
            return self._factory_to_factory_with_config(service_id, factory)

        return factory_with_config_provider


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
