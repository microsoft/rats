from abc import abstractmethod
from dataclasses import dataclass
from typing import Protocol, TypeVar


class IExecutePipelineNodes(Protocol):
    @abstractmethod
    def execute_node(self) -> None:
        pass


class IPipelineNode(IExecutePipelineNodes, Protocol):
    pass


PipelineNodeType = TypeVar("PipelineNodeType", bound=IPipelineNode)


class IProvidePipelineNodes(Protocol[PipelineNodeType]):
    @abstractmethod
    def get_pipeline_node(self) -> PipelineNodeType:
        pass
