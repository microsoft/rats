from typing import Any, Iterable, Mapping, Tuple, TypeVar

import oneml.pipelines as op

from ._pipeline import PDependency, Pipeline, PNode, PNodeProperties

T = TypeVar("T", bound=Mapping[str, Any], covariant=True)
TI = TypeVar("TI", contravariant=True)  # generic input types for processor
TO = TypeVar("TO", covariant=True)  # generic output types for processor


class P2Pipeline:
    @staticmethod
    def node(node: PNode) -> op.PipelineNode:
        return op.PipelineNode(repr(node))

    @classmethod
    def dependencies(
        cls, dependencies: Iterable[PDependency[TI, TO]]
    ) -> Tuple[op.PipelineNode, ...]:
        if any(dp.node is None for dp in dependencies):
            raise ValueError("Trying to register a hanging depencency.")
        return tuple(cls.node(dp.node) for dp in dependencies if dp.node)


class PipelineNodeClient(op.PipelineNodeClient):
    def __init__(self, nodes: Iterable[PNode]) -> None:
        super().__init__()
        for node in nodes:
            self.register_node(P2Pipeline.node(node))


class PipelineNodeDependenciesClient(op.PipelineNodeDependenciesClient):
    def __init__(
        self,
        node_client: op.ILocatePipelineNodes,
        dependencies: Mapping[PNode, Iterable[PDependency[TI, TO]]],
    ) -> None:
        super().__init__(node_client)
        for node, dps in dependencies.items():
            node_client.get_node_by_key(P2Pipeline.node(node).key)  # node exists in node_client
            self.register_node_dependencies(P2Pipeline.node(node), P2Pipeline.dependencies(dps))


class PipelineNodeExecutablesClient(op.PipelineNodeExecutablesClient):
    def __init__(self, properties: Mapping[PNode, PNodeProperties[T]]) -> None:
        super().__init__()
        for node, props in properties.items():
            self.register_node_executable(P2Pipeline.node(node), props.exec_provider)


class PipelineClient:
    _node_client: PipelineNodeClient
    _dependencies_client: PipelineNodeDependenciesClient
    _executables_client: PipelineNodeExecutablesClient

    def __init__(self, pipeline: Pipeline[T, TI, TO]) -> None:
        super().__init__()
        self._node_client = PipelineNodeClient(pipeline.nodes)
        self._dependencies_client = PipelineNodeDependenciesClient(
            self._node_client, pipeline.dependencies
        )
        self._executables_client = PipelineNodeExecutablesClient(pipeline.props)
