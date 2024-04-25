from abc import abstractmethod
from collections.abc import Mapping
from typing import Any, Protocol

from . import _typing as rpt


class IPipelineRunner(Protocol):
    @abstractmethod
    def __call__(self, inputs: Mapping[str, Any] = {}) -> Mapping[str, Any]: ...


class IPipelineRunnerFactory(Protocol):
    @abstractmethod
    def __call__(self, pipeline: rpt.UPipeline) -> IPipelineRunner: ...
