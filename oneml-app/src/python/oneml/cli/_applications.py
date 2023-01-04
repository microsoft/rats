from abc import abstractmethod
from typing import Protocol


class IApplication(Protocol):
    @abstractmethod
    def execute(self) -> None:
        """
        Execute an Application.
        """
