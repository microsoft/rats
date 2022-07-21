import base64
import uuid
from collections import defaultdict
from typing import Dict, List, Mapping, Tuple, Union, cast

from oneml.processors.processor import Processor

from .base_dag import InputPortAddress, NodeName, OutputPortAddress, UnverifiedBaseDag
from .dag import DAG
from .flat_dag import FlatDAG
from .identifiers import _level_separator
from .node import InputPortName, OutputPortName


def make_id() -> str:
    return base64.b32encode(uuid.uuid4().bytes).decode("UTF-8")[:16].lower()


class DAGFlattener:
    def flatten(self, dag: DAG) -> FlatDAG:
        def rec(node: Processor) -> Union[Processor, FlatDAG]:
            if node.is_dag():
                return self.flatten(node)
            else:
                return node

        flattened_original_nodes = {
            NodeName(node_name): rec(node) for node_name, node in dag.nodes.items()
        }
        flattened_original_nodes_reversed_input_edges: Dict[
            NodeName, Dict[InputPortName, List[InputPortAddress]]
        ] = defaultdict(lambda: defaultdict(list))
        nodes: Dict[NodeName, Processor] = dict()
        input_edges: Dict[InputPortName, InputPortAddress] = dict()
        edges: Dict[InputPortAddress, OutputPortAddress] = dict()
        output_edges: Dict[OutputPortName, OutputPortAddress] = dict()
        for node_name, node in flattened_original_nodes.items():
            if node.is_dag():
                node = cast(FlatDAG, node)
                for internal_node_name, internal_node in node.nodes.items():
                    nodes[node_name + internal_node_name] = internal_node
                for (
                    internal_input_port_address,
                    internal_output_port_address,
                ) in node.edges.items():
                    edges[
                        node_name + internal_input_port_address
                    ] = node_name + internal_output_port_address
                for (
                    internal_input_port_address,
                    internal_input_port_name,
                ) in node.input_edges.items():
                    flattened_original_nodes_reversed_input_edges[node_name][
                        internal_input_port_name
                    ].append(internal_input_port_address)
            else:
                nodes[node_name] = node

        for input_port_address, input_port_name in dag.input_edges.items():
            target_node_name = input_port_address.node
            target_port = input_port_address.port
            target_node = flattened_original_nodes[target_node_name]
            if target_node.is_dag():
                for internal_input_port_address in flattened_original_nodes_reversed_input_edges[
                    target_node_name
                ][target_port]:
                    input_port_address = target_node_name + internal_input_port_address
                    input_edges[input_port_address] = input_port_name
            else:
                input_edges[input_port_address] = input_port_name

        for input_port_address, output_port_address in dag.edges.items():
            source_node_name = output_port_address.node
            source_port = output_port_address.port
            source_node = flattened_original_nodes[source_node_name]
            if source_node.is_dag():
                internal_output_port_address = source_node.output_edges[source_port]
                output_port_address = source_node_name + internal_output_port_address
            target_node_name = input_port_address.node
            target_port = input_port_address.port
            target_node = flattened_original_nodes[target_node_name]
            if target_node.is_dag():
                for internal_input_port_address in flattened_original_nodes_reversed_input_edges[
                    target_node_name
                ][target_port]:
                    input_port_address = target_node_name + internal_input_port_address
                    edges[input_port_address] = output_port_address
            else:
                edges[input_port_address] = output_port_address

        for output_port_name, output_port_address in dag.output_edges.items():
            source_node_name = output_port_address.node
            source_port = output_port_address.port
            source_node = flattened_original_nodes[source_node_name]
            if source_node.is_dag():
                internal_output_port_address = source_node.output_edges[source_port]
                output_port_address = source_node_name + internal_output_port_address
            output_edges[output_port_name] = output_port_address
        return FlatDAG(
            nodes=nodes, input_edges=input_edges, output_edges=output_edges, edges=edges
        )

    def break_to_clusters(
        self, flat_dag: FlatDAG, node_to_cluster: Mapping[NodeName, Tuple[NodeName, NodeName]]
    ) -> UnverifiedBaseDag[NodeName]:
        nodes = dict()
        clusters = defaultdict(
            lambda: UnverifiedBaseDag[NodeName](
                nodes={},
                input_edges={},
                edges={},
                output_edges={},
            )
        )
        input_edges = dict()
        edges = dict()
        output_edges = dict()
        for node_name, node in flat_dag.nodes.items():
            broken_node_name = node_to_cluster.get(node_name, None)
            if broken_node_name is None:
                nodes[node_name] = node
            else:
                cluster_name, rest_of_name = broken_node_name
                clusters[cluster_name].nodes[NodeName(rest_of_name)] = node
        for port_address, port_name in flat_dag.input_edges.items():
            node_name = port_address.node
            port_name_in_node = port_address.port
            broken_node_name = node_to_cluster.get(node_name, None)
            if broken_node_name is None:
                input_edges[port_address] = port_name
            else:
                cluster_name, rest_of_name = broken_node_name
                # TODO: change flatten to store the DAG port name somewhere, then use it here.
                port_name_in_cluster = InputPortName(make_id())
                clusters[cluster_name].input_edges[
                    InputPortAddress(rest_of_name, port_name_in_node)
                ] = port_name_in_cluster
                input_edges[InputPortAddress(cluster_name, port_name_in_cluster)] = port_name
        for port_name, port_address in flat_dag.output_edges.items():
            node_name = port_address.node
            port_name_in_node = port_address.port
            broken_node_name = node_to_cluster.get(node_name, None)
            if broken_node_name is None:
                output_edges[port_name] = port_address
            else:
                cluster_name, rest_of_name = broken_node_name
                # TODO: change flatten to store the DAG port name somewhere, then use it here.
                port_name_in_cluster = OutputPortName(make_id())
                clusters[cluster_name].output_edges[port_name_in_cluster] = OutputPortAddress(
                    rest_of_name, port_name_in_node
                )
                output_edges[port_name] = OutputPortAddress(cluster_name, port_name_in_cluster)
        for input_port_address, output_port_address in flat_dag.edges.items():
            input_node_name = input_port_address.node
            port_name_in_input_node = input_port_address.port
            output_node_name = output_port_address.node
            port_name_in_output_node = output_port_address.port
            broken_input_node_name = node_to_cluster.get(input_node_name, None)
            broken_output_node_name = node_to_cluster.get(output_node_name, None)
            if (
                broken_input_node_name is not None
                and broken_output_node_name is not None
                and broken_input_node_name[0] == broken_output_node_name[0]
            ):
                cluster_name = broken_input_node_name[0]
                input_node_rest_of_name = broken_input_node_name[1]
                output_node_rest_of_name = broken_output_node_name[1]
                clusters[cluster_name].edges[
                    InputPortAddress(input_node_rest_of_name, port_name_in_input_node)
                ] = OutputPortAddress(output_node_rest_of_name, port_name_in_output_node)
            else:
                if broken_input_node_name is not None:
                    cluster_name, rest_of_name = broken_input_node_name
                    # TODO: change flatten to store the DAG port name somewhere, then use it here.
                    port_name_in_cluster = InputPortName(make_id())
                    clusters[cluster_name].input_edges[
                        InputPortAddress(rest_of_name, port_name_in_input_node)
                    ] = port_name_in_cluster
                    input_port_address = InputPortAddress(cluster_name, port_name_in_cluster)
                if broken_output_node_name is not None:
                    cluster_name, rest_of_name = broken_output_node_name
                    # TODO: change flatten to store the DAG port name somewhere, then use it here.
                    port_name_in_cluster = OutputPortName(make_id())
                    clusters[cluster_name].output_edges[port_name_in_cluster] = OutputPortAddress(
                        rest_of_name, port_name_in_output_node
                    )
                    output_port_address = OutputPortAddress(cluster_name, port_name_in_cluster)
                edges[input_port_address] = output_port_address
        for cluster_name, unverified_dag in clusters.items():
            cluster_flat_dag = FlatDAG(
                nodes=unverified_dag.nodes,
                input_edges=unverified_dag.input_edges,
                edges=unverified_dag.edges,
                output_edges=unverified_dag.output_edges,
            )
            nodes[cluster_name] = cluster_flat_dag
        return UnverifiedBaseDag[NodeName](
            nodes=nodes, input_edges=input_edges, edges=edges, output_edges=output_edges
        )

    def unflatten(self, flat_dag: FlatDAG) -> DAG:
        cluster_names = set()
        node_to_cluster = dict()
        for node_name in flat_dag.nodes.keys():
            levels = node_name.split(_level_separator, 1)
            if len(levels) == 2:
                cluster_name = NodeName(levels[0])
                rest_of_name = NodeName(levels[1])
                node_to_cluster[node_name] = (cluster_name, rest_of_name)
                cluster_names.add(cluster_name)
        unverified_dag = self.break_to_clusters(flat_dag, node_to_cluster)
        nodes = unverified_dag.nodes
        for cluster_name in cluster_names:
            cluster_dag = self.unflatten(nodes[cluster_name])
            nodes[cluster_name] = cluster_dag
        return DAG(
            nodes=nodes,
            input_edges=unverified_dag.input_edges,
            edges=unverified_dag.edges,
            output_edges=unverified_dag.output_edges,
        )
