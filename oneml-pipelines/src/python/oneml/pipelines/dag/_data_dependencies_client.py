from typing import Any

from ._structs import PipelineDataDependency, PipelineNode


class PipelineDataDependenciesClient:
    _dependencies: dict[PipelineNode, tuple[PipelineDataDependency[Any], ...]]

    def __init__(self) -> None:
        self._dependencies = {}

    def register_data_dependencies(
        self, node: PipelineNode, dependencies: tuple[PipelineDataDependency[Any], ...]
    ) -> None:
        if node in self._dependencies:
            raise RuntimeError(f"Duplicate dependency found: {node}")

        self._dependencies[node] = dependencies

    def get_node_dependencies(self, node: PipelineNode) -> tuple[PipelineDataDependency[Any], ...]:
        return self._dependencies.get(node, tuple())
