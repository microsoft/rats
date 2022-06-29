import logging
from collections import defaultdict
from typing import Any, Dict, List, Sequence, Tuple, Union

from munch import munchify
from networkx import DiGraph
from networkx.algorithms.dag import topological_sort

from .base_dag import InputPortAddress, OutputPortAddress
from .dag import DAG, NodeName
from .dag_runner import DAGRunner
from .flat_dag import _FlatDAG
from .processor import OutputPortName
from .run_context import RunContext

logger = logging.getLogger(__name__)


class TopologicalSortDAGRunner(DAGRunner):
    def _get_mapping_from_node_output_names(
        self, dag: _FlatDAG
    ) -> Dict[OutputPortAddress, List[Union[InputPortAddress, OutputPortName]]]:
        d = defaultdict(list)
        for targetPortAddres, sourcePortAddress in dag.edges.items():
            d[sourcePortAddress].append(targetPortAddres)
        for outputPortName, sourcePortAddress in dag.output_edges.items():
            d[sourcePortAddress].append(outputPortName)
        return d

    def _get_node_edges(self, dag: _FlatDAG) -> Sequence[Tuple[NodeName, NodeName]]:
        edges = (
            [
                ("***source***", inputPortAddres.node)
                for inputPortAddres, _ in dag.input_edges.items()
            ]
            + [
                (sourcePortAddress.node, targetPortAddres.node)
                for targetPortAddres, sourcePortAddress in dag.edges.items()
            ]
            + [
                (outputPortAddress.node, "***target***")
                for _, outputPortAddress in dag.output_edges.items()
            ]
        )
        return list(set(edges))

    def _get_digraph(self, dag: _FlatDAG) -> DiGraph:
        return DiGraph(self._get_node_edges(dag))

    def _get_processing_order(self, dag: _FlatDAG) -> Sequence[NodeName]:
        g = self._get_digraph(dag)
        nodes_in_topological_order = [
            node_name
            for node_name in topological_sort(g)
            if node_name not in ["***source***", "***target***"]
        ]
        return nodes_in_topological_order

    def run(self, dag: DAG, run_context: RunContext, **inputs: Any) -> Dict[OutputPortName, Any]:
        flattened_dag = dag._flatten()
        outputs = self._run_flattened(flattened_dag, run_context, **inputs)
        return outputs

    def _run_flattened(
        self, dag: _FlatDAG, run_context: RunContext, **inputs: Any
    ) -> Dict[OutputPortName, Any]:
        edges_dict = self._get_mapping_from_node_output_names(dag)
        data_dict: Dict[Union[InputPortAddress, OutputPortName], Any] = dict()
        for inputPortAddress, inputPortName in dag.input_edges.items():
            logger.debug("adding data for %s", inputPortAddress)
            data_dict[inputPortAddress] = inputs[inputPortName]
        for node_name in self._get_processing_order(dag):
            logger.debug("calling %s", node_name)
            node = dag.nodes[node_name]
            node_inputs = {
                input_name_in_node: data_dict[InputPortAddress(node_name, input_name_in_node)]
                for input_name_in_node in node.get_input_schema().keys()
            }
            node_outputs = node.process(run_context.add_identifier_level(node_name), **node_inputs)
            for output_name_in_node, output_value in node_outputs.items():
                targets = edges_dict[OutputPortAddress(node_name, output_name_in_node)]
                for target in targets:
                    logger.debug("adding data for %s", target)
                    data_dict[target] = output_value
        export_outputs = munchify(
            {
                export_name: data_dict[OutputPortName(export_name)]
                for export_name in dag.get_output_schema().keys()
            }
        )
        return export_outputs
