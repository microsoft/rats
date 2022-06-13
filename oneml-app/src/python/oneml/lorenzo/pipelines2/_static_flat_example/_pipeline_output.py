from abc import ABC, abstractmethod
from typing import Type, TypeVar

OutputType = TypeVar("OutputType")


class PipelineOutput(ABC):
    @abstractmethod
    def add(self, name: Type[OutputType], value: OutputType) -> None:
        pass
