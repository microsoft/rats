from dataclasses import dataclass
from typing import Any, Dict, Generic, Tuple, TypeVar

from ._structs import PipelineNode

# TODO: Remove the copies of DataType and PipelineDataNode from session package
PipelinePortDataType = TypeVar("PipelinePortDataType")


@dataclass(frozen=True)
class PipelinePort(Generic[PipelinePortDataType]):
    key: str


@dataclass(frozen=True)
class PipelineDataDependency(Generic[PipelinePortDataType]):
    node: PipelineNode
    output_port: PipelinePort[PipelinePortDataType]
    input_port: PipelinePort[PipelinePortDataType]


class PipelineDataDependenciesClient:

    _dependencies: Dict[PipelineNode, Tuple[PipelineDataDependency[Any], ...]]

    def __init__(self) -> None:
        self._dependencies = {}

    def register_data_dependencies(
            self,
            node: PipelineNode,
            dependencies: Tuple[PipelineDataDependency[Any], ...]) -> None:
        if node in self._dependencies:
            raise RuntimeError(f"Duplicate dependency found: {node}")

        self._dependencies[node] = dependencies

    def get_node_dependencies(
            self, node: PipelineNode) -> Tuple[PipelineDataDependency[Any], ...]:
        return self._dependencies.get(node, tuple())
