# type: ignore
# flake8: noqa
from collections import defaultdict
from typing import Callable, Dict, Set, Type

from oneml.processors.run_context import RunContext

from ..processors import (
    DAG,
    Data,
    FlatDAG,
    InputPortName,
    NodeName,
    OutputPortName,
    Processor,
    processor,
)


def find_downstream_nodes_for_input_ports(
    flat_dag: FlatDAG, input_port_filter: Callable[[str], bool]
) -> Set[NodeName]:
    reverse_edges = defaultdict(list)
    for input_port_address, output_port_address in flat_dag.edges.items():
        source = output_port_address.node
        target = input_port_address.node
        reverse_edges[source].append(target)
    downstream_nodes = set()

    def dfs_nodes(source):
        if source in downstream_nodes:
            return
        else:
            downstream_nodes.add(source)
            for target in reverse_edges[source]:
                dfs_nodes(target)

    for input_port_address, input_port_name in flat_dag.input_edges.items():
        if input_port_filter(input_port_name):
            target = input_port_address.node
            dfs_nodes(target)
    return downstream_nodes


@processor
class WithPortsRenamed:
    def __init__(
        self,
        processor: Processor,
        input_ports_rename: Callable[[InputPortName], InputPortName],
        output_ports_rename: Callable[[OutputPortName], OutputPortName],
    ):
        self.wrapped_processor = processor
        self._input_ports_rename = input_ports_rename
        self._output_ports_rename = output_ports_rename
        self._name = processor.name

    def get_input_schema(self) -> Dict[InputPortName, Type[Data]]:
        return {
            self._input_ports_rename(input_port_name): t
            for input_port_name, t in self.wrapped_processor.get_input_schema().items()
        }

    def get_output_schema(self) -> Dict[OutputPortName, Type[Data]]:
        return {
            self._output_ports_rename(output_port_name): t
            for output_port_name, t in self.wrapped_processor.get_output_schema().items()
        }

    def process(self, run_context: RunContext, **inputs: Data) -> Dict[OutputPortName, Data]:
        renamed_inputs = {
            input_port_name: inputs[self._input_ports_rename(input_port_name)]
            for input_port_name in self.wrapped_processor.get_input_schema().keys()
        }
        outputs = self.wrapped_processor.process(run_context, **renamed_inputs)
        renamed_outputs = {
            self._output_ports_rename(output_port_name): value
            for output_port_name, value in outputs.items()
        }
        return renamed_outputs


def with_ports_renamed(
    processor: Processor,
    input_ports_rename: Callable[[str], str],
    output_ports_rename: Callable[[str], str],
) -> Processor:
    def _input_ports_rename(input_port_name: InputPortName) -> InputPortName:
        return InputPortName(input_ports_rename(input_port_name))

    def _output_ports_rename(output_port_name: OutputPortName) -> OutputPortName:
        return OutputPortName(output_ports_rename(output_port_name))

    if processor.is_dag():
        nodes = processor.nodes
        input_edges = {
            input_port_address: _input_ports_rename(input_port_name)
            for input_port_address, input_port_name in processor.input_edges.items()
        }
        edges = processor.edges
        output_edges = {
            _output_ports_rename(output_port_name): output_ports_address
            for output_port_name, output_ports_address in processor.output_edges.items()
        }
        wrapper_processor = DAG(
            nodes=nodes, input_edges=input_edges, edges=edges, output_edges=output_edges
        )
    else:
        wrapper_processor = WithPortsRenamed(
            processor,
            _input_ports_rename,
            _output_ports_rename,
        )
    return wrapper_processor
