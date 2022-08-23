from dataclasses import dataclass
from typing import Dict, Generic, Set, Tuple, TypeVar

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

    _dependencies: Dict[PipelineNode, Set[PipelineDataDependency]]

    def register_data_dependency(
            self,
            pipeline_node: PipelineNode,
            dependency: PipelineDataDependency) -> None:
        current = self._dependencies.get(pipeline_node, set())
        if dependency in current:
            raise RuntimeError(f"Duplicate dependency found: {pipeline_node} -> {dependency}")

        current.add(dependency)
        self._dependencies[pipeline_node] = current

    def get_node_dependencies(
            self, pipeline_node: PipelineNode) -> Tuple[PipelineDataDependency, ...]:
        return tuple(self._dependencies.get(pipeline_node, set()))
