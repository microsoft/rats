from abc import abstractmethod
from typing import Generic, Protocol, TypeVar


class IExecutePipelines(Protocol):
    @abstractmethod
    def execute_pipeline(self) -> None:
        pass


class IPipeline(IExecutePipelines, Protocol):
    pass


PipelineType = TypeVar("PipelineType", bound=IPipeline)


class IProvidePipelines(Protocol[PipelineType]):
    @abstractmethod
    def get_pipeline(self) -> PipelineType:
        pass
