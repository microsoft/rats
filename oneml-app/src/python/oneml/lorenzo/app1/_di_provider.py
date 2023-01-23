from abc import abstractmethod
from typing import Protocol

from ._executables import App1PipelineExecutables


class DiProvider(Protocol):
    @abstractmethod
    def pipeline_executables(self) -> App1PipelineExecutables:
        pass
