# type: ignore
# flake8: noqa
import logging
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Dict, List, Sequence, Tuple, Type, Union

from munch import munchify
from networkx import DiGraph
from networkx.algorithms.dag import topological_sort

from .processors import Processor

logger = logging.getLogger(__name__)


@dataclass
class DAG(Processor):
    nodes: Dict[str, Processor]
    edges: Sequence[Tuple[Tuple[str, str], Tuple[str, str]]]
    inputs: Sequence[Tuple[str, Tuple[str, str]]]
    outputs: Sequence[Tuple[str, Tuple[str, str]]]

    def get_input_schema(self) -> Dict[str, Type]:
        return {
            export_name: self.nodes[node_name].get_input_schema()[input_name_in_node]
            for export_name, (node_name, input_name_in_node) in self.inputs
        }

    def get_output_schema(self) -> Dict[str, Type]:
        return {
            export_name: self.nodes[node_name].get_output_schema()[output_name_in_node]
            for export_name, (node_name, output_name_in_node) in self.outputs
        }

    def _get_mapping_from_node_output_names(
        self,
    ) -> Dict[Tuple[str, str], List[Union[str, Tuple[str, str]]]]:
        d = defaultdict(list)
        for (
            (source_node_name, output_name_in_source),
            (target_node_name, input_name_in_target),
        ) in self.edges:
            d[(source_node_name, output_name_in_source)].append(
                (target_node_name, input_name_in_target)
            )
        for export_name, (node_name, output_name_in_node) in self.outputs:
            d[(node_name, output_name_in_node)].append(export_name)
        return d

    def _get_node_edges(self) -> Sequence[Tuple[str, str]]:
        edges = (
            [
                ("***source***", target_node_name)
                for _, (target_node_name, input_name_in_target) in self.inputs
            ]
            + [
                (source_node_name, target_node_name)
                for (
                    (source_node_name, output_name_in_source),
                    (target_node_name, input_name_in_target),
                ) in self.edges
            ]
            + [
                (source_node_name, "***target***")
                for _, (source_node_name, output_name_in_source) in self.outputs
            ]
        )
        return list(set(edges))

    def _get_digraph(self) -> DiGraph:
        return DiGraph(self._get_node_edges())

    def _get_processing_order(self) -> Sequence[str]:
        g = self._get_digraph()
        return list(topological_sort(g))[1:-1]

    def process(self, **kwds: Any) -> Dict[str, Type]:
        edges_dict = self._get_mapping_from_node_output_names()
        data_dict = dict()
        for export_name, (node_name, input_name_in_node) in self.inputs:
            logger.debug("adding data for %s", (node_name, input_name_in_node))
            data_dict[(node_name, input_name_in_node)] = kwds[export_name]
        for node_name in self._get_processing_order():
            logger.debug("calling %s", node_name)
            node = self.nodes[node_name]
            node_inputs = {
                input_name_in_node: data_dict[(node_name, input_name_in_node)]
                for input_name_in_node in node.get_input_schema().keys()
            }
            node_outputs = node.process(**node_inputs)
            for output_name_in_node, output_value in node_outputs.items():
                targets = edges_dict[(node_name, output_name_in_node)]
                for target in targets:
                    logger.debug("adding data for %s", target)
                    data_dict[target] = output_value
        export_outputs = munchify(
            {
                export_name: data_dict[export_name]
                for export_name in self.get_output_schema().keys()
            }
        )
        return export_outputs
