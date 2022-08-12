from dataclasses import dataclass
from typing import Protocol, Tuple

from oneml.pipelines import IExecutable, ITickablePipeline, PipelineNode


@dataclass(frozen=True)
class PipelineNodeDependencies:
    node: PipelineNode
    dependencies: Tuple[PipelineNode, ...]


@dataclass(frozen=True)
class PipelineNodeExecutable:
    node: PipelineNode
    executable: IExecutable


class IProvidePipelineComponents(Protocol):
    def nodes(self) -> Tuple[PipelineNode, ...]:
        pass

    def dependencies(self) -> Tuple[PipelineNodeDependencies, ...]:
        pass

    def executables(self) -> Tuple[PipelineNodeExecutable, ...]:
        pass


class ExamplePipeline(ITickablePipeline):

    def tick(self) -> None:
        pass


class ExamplePipelineBuilder:

    def build(self, config: IProvidePipelineComponents) -> ITickablePipeline:
        pass
