from typing import Callable

from ..processors import DAG, DAGFlattener, FlatDAG, InputPortAddress, NodeName, OutputPortAddress
from .utils import find_downstream_nodes_for_input_ports


class WithInputsDuplicated(DAG):
    """A DAG that handles 0 or more copies of a subset of a given DAG's inputs.

    Args:
        dag: The original DAG to process
        input_port_filter: A function taking an input port name and deciding whether it should be
            duplicated.  The set of input ports selected by the function will define the sub-graph
            that will be duplicated.  Any node and output port that is downstream of any of of the
            selected input ports will be part of the duplicated sub-graph.
        K: number of copies to create of the sub-graph to duplicated.  If K=0, then the sub-graph
            and selected input nodes will be removed.
        port_rename: A function taking a port name and an integer in [0, K) and returning a new
            port name.  Will be applied to both input ports and output ports of the duplicated
            subgraph.  Ignored if K=0.
    """

    def __init__(
        self,
        dag: DAG,
        input_port_filter: Callable[[str], bool],
        port_rename: Callable[[str, int], str],
        K: int,
    ):
        dag_flattener = DAGFlattener()
        flat_dag = dag_flattener.flatten(dag)

        def get_multiplexed_node_name(node_name: NodeName, k: int) -> NodeName:
            return NodeName(f"{node_name}_{k:05}")

        multiplex_nodes = find_downstream_nodes_for_input_ports(flat_dag, input_port_filter)
        nodes = dict()
        for node_name, node in flat_dag.nodes.items():
            if node_name not in multiplex_nodes:
                nodes[node_name] = node
            else:
                for k in range(K):
                    nodes[get_multiplexed_node_name(node_name, k)] = node
        input_edges = dict()
        for input_port_address, input_port_name in flat_dag.input_edges.items():
            source_port = input_port_name
            target_node = input_port_address.node
            target_port = input_port_address.port
            if target_node not in multiplex_nodes:
                input_edges[input_port_address] = input_port_name
            else:
                for k in range(K):
                    input_port_address = InputPortAddress(
                        get_multiplexed_node_name(target_node, k), target_port
                    )
                    if input_port_filter(source_port):
                        input_port_name = port_rename(source_port, k)
                    input_edges[input_port_address] = input_port_name
        edges = dict()
        for input_port_address, output_port_address in flat_dag.edges.items():
            target_node = input_port_address.node
            target_port = input_port_address.port
            source_node = output_port_address.node
            source_port = output_port_address.port
            if target_node not in multiplex_nodes:
                assert source_node not in multiplex_nodes
                edges[input_port_address] = output_port_address
            else:
                for k in range(K):
                    input_port_address = InputPortAddress(
                        get_multiplexed_node_name(target_node, k), target_port
                    )
                    if source_node in multiplex_nodes:
                        output_port_address = OutputPortAddress(
                            get_multiplexed_node_name(source_node, k), source_port
                        )
                    edges[input_port_address] = output_port_address
        output_edges = dict()
        for output_port_name, output_port_address in flat_dag.output_edges.items():
            source_node = output_port_address.node
            source_port = output_port_address.port
            target_port = output_port_name
            if source_node not in multiplex_nodes:
                output_edges[output_port_name] = output_port_address
            else:
                for k in range(K):
                    output_port_address = OutputPortAddress(
                        get_multiplexed_node_name(source_node, k), source_port
                    )
                    output_port_name = port_rename(target_port, k)
                    output_edges[output_port_name] = output_port_address
        flat_dag = FlatDAG(
            nodes=nodes, input_edges=input_edges, edges=edges, output_edges=output_edges
        )
        dag = dag_flattener.unflatten(flat_dag)
        super().__init__(
            nodes=dag.nodes,
            input_edges=dag.input_edges,
            edges=dag.edges,
            output_edges=dag.output_edges,
        )
