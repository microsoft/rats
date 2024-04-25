from collections.abc import Mapping
from typing import Protocol, TypeVar, runtime_checkable

from rats.processors._legacy_subpackages.ux import NoInputs, Outputs, Pipeline, UPipeline

Tco_Pipeline = TypeVar("Tco_Pipeline", bound=UPipeline, covariant=True)
Tconra_Pipeline = TypeVar("Tconra_Pipeline", bound=UPipeline, contravariant=True)

ExecutablePipeline = Pipeline[NoInputs, Outputs]


@runtime_checkable
class IProvidePipeline(Protocol[Tco_Pipeline]):
    def __call__(self) -> Tco_Pipeline: ...


@runtime_checkable
class ITransformPipeline(Protocol[Tconra_Pipeline, Tco_Pipeline]):
    def __call__(self, pipeline: Tconra_Pipeline) -> Tco_Pipeline: ...


IProvidePipelineCollection = Mapping[str, IProvidePipeline[UPipeline]]
