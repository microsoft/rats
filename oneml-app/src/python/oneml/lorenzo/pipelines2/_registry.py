from typing import Dict, Iterable, Tuple, Type

from ._node import IProvidePipelineNodes, PipelineNodeType
from ._pipeline import IProvidePipelines, PipelineType


class PipelineRegistry:
    _pipelines: Dict[Type[PipelineType], IProvidePipelines[PipelineType]]

    def __init__(self):
        self._pipelines = {}

    def register(self, key: Type[PipelineType], provider: IProvidePipelines[PipelineType]) -> None:
        if key in self._pipelines:
            raise RuntimeError(f"Node already registered: {key}")

        self._pipelines[key] = provider

    def get(self, key: Type[PipelineType]) -> PipelineType:
        return self._pipelines[key].get_pipeline()


class PipelineNodeDag:

    _nodes: Dict[Type[PipelineNodeType], IProvidePipelineNodes]
    _edges: Dict[Type[PipelineNodeType], Tuple[Type[PipelineNodeType], ...]]

    def __init__(
            self,
            nodes: Dict[Type[PipelineNodeType], IProvidePipelineNodes],
            edges: Dict[Type[PipelineNodeType], Tuple[Type[PipelineNodeType], ...]]):
        self._nodes = nodes
        self._edges = edges
        """
        Example of composability:
        - TCR Selection (filters TCRs)
        - HPO that is composing a DAG (No Deps)
            - Step 1 (No Task Deps, Needs a slice of parameters from HPO)
            - Step 2 (Depends on TCR Selection)
        """

    def get_items(
            self) -> Iterable[Tuple[PipelineNodeType, IProvidePipelineNodes[PipelineNodeType]]]:
        traversed = ()
        while len(traversed) < len(self._nodes.keys()):
            processable_nodes = self._get_nodes_with_edges(traversed)
            if len(processable_nodes) == 0:
                raise RuntimeError("Broken DAG? Not all nodes processable.")

            keys = [k for k, _ in processable_nodes]
            print(f"processable this iteration: {keys}")
            for key, provider in processable_nodes:
                print(key)
                traversed = tuple([x for x in traversed] + [key])
                yield key, provider

    def _get_nodes_with_edges(
            self, edges: Tuple[PipelineNodeType, ...]
    ) -> Tuple[Tuple[Type[IProvidePipelineNodes], IProvidePipelineNodes[PipelineNodeType]], ...]:
        inbound_edges = set(edges)
        result = []
        for key, provider in self._nodes.items():
            if key in inbound_edges:
                continue

            # If the node is not in `_edges`, it has empty tuple of dependencies
            node_edges = set(self._edges.get(key, ()))
            # Yield all nodes that require `iteration_traversed` as input
            if node_edges.issubset(inbound_edges):
                result.append((key, provider))

        return tuple(result)


class PipelineNodeDagBuilder:

    _nodes: Dict[Type[PipelineNodeType], IProvidePipelineNodes]
    _edges: Dict[Type[PipelineNodeType], Tuple[Type[PipelineNodeType], ...]]

    def __init__(self):
        self._nodes = {}
        self._edges = {}

    def register_node(
            self,
            key: Type[PipelineNodeType],
            provider: IProvidePipelineNodes[PipelineNodeType]) -> None:

        if key in self._nodes:
            raise RuntimeError(f"Node already registered: {key}")

        self._nodes[key] = provider

    def register_edges(self, key: Type[PipelineNodeType], inputs: Tuple[Type, ...]) -> None:
        if key in self._edges:
            raise RuntimeError(f"Node edges already registered: {key}")

        self._edges[key] = inputs

    def build(self) -> PipelineNodeDag:
        return PipelineNodeDag(self._nodes, self._edges)


class DynamicPipelineNodeDag:
    pass
