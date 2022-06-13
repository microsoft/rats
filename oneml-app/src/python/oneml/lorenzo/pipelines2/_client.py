from abc import abstractmethod
from typing import Protocol, Type

from ._pipeline import PipelineType
from ._registry import PipelineRegistry


class IPipelineClient(Protocol):

    @abstractmethod
    def execute(self, key: Type[PipelineType]) -> None:
        pass


class LocalPipelineClient(IPipelineClient):
    _registry: PipelineRegistry

    def __init__(self, registry: PipelineRegistry):
        self._registry = registry

    def execute(self, key: Type[PipelineType]) -> None:
        self._registry.get(key).execute_pipeline()
