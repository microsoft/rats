import logging
from abc import abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Generic, Protocol, TypeVar

logger = logging.getLogger(__name__)
ComponentType = TypeVar("ComponentType")


@dataclass(frozen=True)
class ComponentId(Generic[ComponentType]):
    key: str


class IProvideSessionComponents(Protocol):
    @abstractmethod
    def get_component(self, component_id: ComponentId[ComponentType]) -> ComponentType:
        pass


class SessionComponents(IProvideSessionComponents):

    _components: Dict[ComponentId[Any], Any]

    def __init__(self) -> None:
        self._components = {}

    def add_component(self, name: ComponentId[ComponentType], component: ComponentType) -> None:
        if name in self._components:
            raise RuntimeError(f"Component with name {name} already exists")

        logger.debug(f"Adding component {name} to session components")
        self._components[name] = component

    def get_component(self, name: ComponentId[ComponentType]) -> ComponentType:
        if name not in self._components:
            raise RuntimeError(f"Component with name {name} does not exist")

        return self._components[name]
