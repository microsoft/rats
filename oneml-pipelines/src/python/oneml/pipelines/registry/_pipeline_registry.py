from abc import abstractmethod
from typing import Protocol

from ._structs import PipelineId


class IProvidePipelines(Protocol):
    @abstractmethod
    def find_pipeline(self, pipeline_id: PipelineId) -> None:
        pass


class PipelineRegistry:
    pass
