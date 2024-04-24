from abc import abstractmethod
from collections.abc import Mapping
from typing import Any, Protocol

import pydot

from rats.processors import _typing as rpt


class IPipelineRunner(Protocol):
    @abstractmethod
    def __call__(self, inputs: Mapping[str, Any] = {}) -> Mapping[str, Any]: ...


class IPipelineRunnerFactory(Protocol):
    @abstractmethod
    def __call__(self, pipeline: rpt.UPipeline) -> IPipelineRunner: ...


class IPipelineToDot(Protocol):
    @abstractmethod
    def __call__(self, pipeline: rpt.UPipeline, include_optional: bool = True) -> pydot.Dot: ...
