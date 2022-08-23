from dataclasses import dataclass
from typing import Dict, Generic, Tuple, TypeVar

from ._structs import PipelineNode

# TODO: Remove the copies of DataType and PipelineDataNode from session package
DataType = TypeVar("DataType")


@dataclass(frozen=True)
class PipelineDataNode(Generic[DataType]):
    key: str


@dataclass(frozen=True)
class PipelineDataDependency(Generic[DataType]):
    pipeline_node: PipelineNode
    data_node: PipelineDataNode[DataType]


class PipelineDataDependenciesClient:

    _dependencies: Dict[PipelineNode, Tuple[PipelineDataDependency, ...]]

    def __init__(self) -> None:
        self._dependencies = {}

    def register_data_dependencies(
            self,
            pipeline_node: PipelineNode,
            dependencies: Tuple[PipelineDataDependency, ...]) -> None:
        if pipeline_node in self._dependencies:
            raise RuntimeError(f"Duplicate dependency found: {pipeline_node}")

        self._dependencies[pipeline_node] = dependencies

    def get_node_dependencies(
            self, pipeline_node: PipelineNode) -> Tuple[PipelineDataDependency, ...]:
        return self._dependencies.get(pipeline_node, tuple())
