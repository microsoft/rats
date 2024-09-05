from collections.abc import Callable
from typing import TypeVar, ParamSpec, Generic, Concatenate
from rats import apps

from ._container import ConfigFactoryContainer


P = ParamSpec("P")
R = TypeVar("R")
S = TypeVar("S")
T_ConfigFactoryContainer = TypeVar("T_ConfigFactoryContainer", bound=ConfigFactoryContainer)


class config_factory_service(Generic[P, R]):
    """A decorator to create a config factory service.

    Decorate a method that takes any number of arguments and returns an object.  The resulting
    service will be that factory - taking the same arguments and returning a new object each time.
    The returned object will hold information about the configuration used to create it, allowing
    IGetConfigurationFromObject to be used to retrieve the configuration.

    Requires the container to be a ConfigFactoryContainer.
    """

    _service_id: apps.ServiceId[Callable[P, R]]

    def __init__(self, service_id: apps.ServiceId[Callable[P, R]]) -> None:
        self._service_id = service_id

    def __call__(
        self, method: Callable[Concatenate[T_ConfigFactoryContainer, P], R]
    ) -> Callable[[T_ConfigFactoryContainer], Callable[P, R]]:
        new_method = self._create_new_method(self._service_id, method)
        return apps.service(self._service_id)(new_method)

    def _create_new_method(
        self,
        service_id: apps.ServiceId[Callable[P, R]],
        method: Callable[Concatenate[T_ConfigFactoryContainer, P], R],
    ) -> Callable[[T_ConfigFactoryContainer], Callable[P, R]]:
        def new_method(self: T_ConfigFactoryContainer) -> Callable[P, R]:
            def factory(*args: P.args, **kwargs: P.kwargs) -> R:
                return method(self, *args, **kwargs)

            factory_with_config = self.factory_to_factory_with_config(
                service_id=service_id, factory=factory
            )
            return factory_with_config

        new_method.__name__ = method.__name__
        new_method.__module__ = method.__module__
        new_method.__qualname__ = method.__qualname__
        new_method.__doc__ = method.__doc__

        return new_method


def autoid_config_factory_service(
    method: Callable[Concatenate[T_ConfigFactoryContainer, P], R],
) -> Callable[[T_ConfigFactoryContainer], Callable[P, R]]:
    """A decorator to create a config factory service, with an automatically generated service id.

    Decorate a method that takes any number of arguments and returns an object.  The resulting
    service will be that factory - taking the same arguments and returning a new object each time.
    The returned object will hold information about the configuration used to create it, allowing
    IGetConfigurationFromObject to be used to retrieve the configuration.

    Requires the container to be a ConfigFactoryContainer.
    """
    module_name = method.__module__
    class_name, method_name = method.__qualname__.rsplit(".", 1)
    service_name = f"{module_name}:{class_name}[{method_name}]"
    service_id = apps.ServiceId[Callable[P, R]](service_name)
    cfs = config_factory_service(service_id)
    return cfs(method)
