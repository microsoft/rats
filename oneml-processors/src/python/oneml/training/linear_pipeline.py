# type: ignore
# flake8: noqa
from typing import Sequence, Tuple

from munch import Munch

from ..processors import DAG, InputPortAddress, OutputPortAddress, Processor


def _get_linear_pipeline(stages: Sequence[Tuple[str, Processor]]):
    nodes = dict(stages)
    latest_output_of_port_name = dict()
    input_edges = dict()
    edges = dict()
    output_edges = dict()
    for node_name, node in stages:
        for port_name in node.get_input_schema().keys():
            port_address = InputPortAddress(node_name, port_name)
            port_source = latest_output_of_port_name.get(port_name, None)
            if port_source is None:
                input_edges[port_address] = port_name
            else:
                edges[port_address] = OutputPortAddress(port_source, port_name)
        for port_name in node.get_output_schema().keys():
            latest_output_of_port_name[port_name] = node_name
            output_edges[port_name] = OutputPortAddress(node_name, port_name)
    return Munch(nodes=nodes, input_edges=input_edges, edges=edges, output_edges=output_edges)


class LinearPipeline(DAG):
    """A linear DAG where nodes are ordered and edges are connecting using port names.

    For stage _i_, input port _p_ is fed from the latest (in terms of stage numbers) output port
    of the same name, up to _i_.  If no such output port exists, _p_ is fed from a DAG input port
    of the same name.
    """

    def __init__(self, stages: Sequence[Tuple[str, Processor]]):
        m = _get_linear_pipeline(stages)
        super().__init__(
            nodes=m.nodes, input_edges=m.input_edges, edges=m.edges, output_edges=m.output_edges
        )
