from typing import Protocol, runtime_checkable

from oneml.processors.ux import UPipeline


@runtime_checkable
class IProvidePipeline(Protocol):
    def __call__(self) -> UPipeline:
        ...


@runtime_checkable
class ITransformPipeline(Protocol):
    def __call__(self, pipeline: UPipeline) -> UPipeline:
        ...


# from typing import Any, Generic, Protocol, TypeVar, runtime_checkable

# from oneml.processors.ux import UPipeline

# Tco_Pipeline = TypeVar("Tco_Pipeline", bound=UPipeline, covariant=True)
# Tcontra_Pipeline = TypeVar("Tcontra_Pipeline", bound=UPipeline, contravariant=True)


# @runtime_checkable
# class IProvidePipeline(Protocol, Generic[Tco_Pipeline]):
#     def __call__(self) -> Tco_Pipeline:
#         ...


# @runtime_checkable
# class ITransformPipeline(Protocol, Generic[Tco_Pipeline, Tcontra_Pipeline]):
#     def __call__(self, pipeline: Tcontra_Pipeline) -> Tco_Pipeline:
#         ...
