from abc import abstractmethod
from collections.abc import Mapping
from typing import Any, Protocol

import pydot

from rats.processors._legacy_subpackages import ux


class IPipelineRunner(Protocol):
    @abstractmethod
    def __call__(self, inputs: Mapping[str, Any] = {}) -> Mapping[str, Any]: ...


class IPipelineRunnerFactory(Protocol):
    @abstractmethod
    def __call__(self, pipeline: ux.UPipeline) -> IPipelineRunner: ...


class IPipelineToDot(Protocol):
    @abstractmethod
    def __call__(self, pipeline: ux.UPipeline, include_optional: bool = True) -> pydot.Dot: ...
