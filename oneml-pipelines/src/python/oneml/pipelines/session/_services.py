import logging
from abc import abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, Dict, Generic, Protocol, TypeVar

logger = logging.getLogger(__name__)
ServiceType = TypeVar("ServiceType")


@dataclass(frozen=True)
class ServiceId(Generic[ServiceType]):
    key: str


class IProvideServices(Protocol):
    @abstractmethod
    def get_service(self, component_id: ServiceId[ServiceType]) -> ServiceType:
        pass


class ServicesRegistry(IProvideServices):

    _services: Dict[ServiceId[Any], Callable[[], Any]]

    def __init__(self) -> None:
        self._services = {}

    def register_service(
        self,
        name: ServiceId[ServiceType],
        provider: Callable[[], ServiceType],
    ) -> None:
        if name in self._services:
            raise RuntimeError(f"Service with name {name} already exists")

        logger.debug(f"Adding service {name} to services registry")
        self._services[name] = provider

    def get_service(self, name: ServiceId[ServiceType]) -> ServiceType:
        if name not in self._services:
            raise RuntimeError(f"Service with name {name} does not exist")

        return self._services[name]()
