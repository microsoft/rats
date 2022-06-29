"""A DAG of processors that is a processor itself."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import TYPE_CHECKING, Dict, List, Tuple, Type

from .base_dag import (
    BaseDAG,
    InputPortAddress,
    NodeName,
    NodeNameT,
    OutputPortAddress,
    SimpleNodeName,
)
from .data_annotation import Data
from .flat_dag import _FlatDAG
from .processor import OutputPortName
from .processor_decorators import processor

if TYPE_CHECKING:
    from .run_context import RunContext


@dataclass
@processor
class DAG(BaseDAG[SimpleNodeName]):
    """A nestable, runnable DAG of Processors."""

    def __post_init__(self) -> None:
        for node_name, node in self.nodes.items():
            if isinstance(node, _FlatDAG):
                raise Exception(
                    f"NestableDAG cannot hold nodes that are FlatDAGs. "
                    f"Node <{node_name}> is a FlatDAG."
                )
        super().__post_init__()

    def _flatten(self) -> _FlatDAG:
        nodes = {NodeName(node_name): node for node_name, node in self.nodes.items()}
        input_edges = self.input_edges.copy()
        output_edges = self.output_edges.copy()
        edges = self.edges.copy()

        node_to_output_edges: Dict[
            NodeName, List[Tuple[OutputPortName, OutputPortAddress]]
        ] = defaultdict(list)
        node_to_edges_to_others: Dict[
            NodeName, List[Tuple[InputPortAddress, OutputPortAddress]]
        ] = defaultdict(list)

        for output_edge in output_edges.items():
            node_name = output_edge[1].node
            node_to_output_edges[node_name].append(output_edge)
        for edge in edges.items():
            from_node_name = edge[1].node
            node_to_edges_to_others[from_node_name].append(edge)

        for node_name in map(NodeName, self.nodes.keys()):
            node = nodes[node_name]
            if hasattr(node, "_flatten"):
                nodes.pop(node_name)
                flattened = node._flatten()
                for internal_node_name, internal_node in flattened.nodes.items():
                    nodes[node_name + internal_node_name] = internal_node
                for (
                    internal_input_port_address,
                    internal_output_port_address,
                ) in flattened.edges.items():
                    input_port_address = node_name + internal_input_port_address
                    output_port_address = node_name + internal_output_port_address
                    edges[input_port_address] = output_port_address
                for internal_edge in flattened.input_edges.items():
                    internal_input_port_address, node_input_port_name = internal_edge
                    input_port_address = InputPortAddress(node_name, node_input_port_name)
                    port_name = input_edges.get(input_port_address, None)
                    if port_name is not None:
                        input_port_address = node_name + internal_input_port_address
                        input_edges[input_port_address] = port_name
                    else:
                        output_port_address = edges.get(input_port_address)
                        input_port_address = node_name + internal_input_port_address
                        edges[input_port_address] = output_port_address
                for output_edge in node_to_output_edges[node_name]:
                    output_port_name, outputNodeAddress = output_edge
                    node_ouput_port_name = outputNodeAddress.port
                    internal_output_port_address = flattened.output_edges[node_ouput_port_name]
                    output_port_address = node_name + internal_output_port_address
                    output_edges[output_port_name] = output_port_address
                for edge in node_to_edges_to_others[node_name]:
                    input_port_address, output_port_address = edge
                    node_output_port_name = output_port_address.port
                    internal_port_address = flattened.output_edges[node_output_port_name]
                    output_port_address = node_name + internal_port_address
                    edges[input_port_address] = output_port_address
                for node_input_port_name in flattened.get_input_schema().keys():
                    input_port_address = InputPortAddress(node_name, node_input_port_name)
                    input_edges.pop(input_port_address, None)
                    edges.pop(input_port_address, None)
        return _FlatDAG(
            nodes=nodes, input_edges=input_edges, output_edges=output_edges, edges=edges
        )

    def _node_name_class(self) -> Type[NodeNameT]:
        return SimpleNodeName

    def process(self, run_context: RunContext, **inputs: Data) -> Dict[OutputPortName, Data]:
        return run_context.run_dag(self, **inputs)
