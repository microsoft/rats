from abc import abstractmethod
from typing import Protocol

from immunodata.cli import GenericContainer, ILocateDiContainers


class ILocateHabitatsCliDiContainer(Protocol):
    @abstractmethod
    def __call__(self, container_ref: type[GenericContainer]) -> GenericContainer:
        pass


class LocateHabitatsCliDiContainers(ILocateHabitatsCliDiContainer):
    _locator: ILocateDiContainers

    def __init__(self, locator: ILocateDiContainers) -> None:
        self._locator = locator

    def __call__(self, container_ref: type[GenericContainer]) -> GenericContainer:
        return self._locator.find_container(container_ref)
