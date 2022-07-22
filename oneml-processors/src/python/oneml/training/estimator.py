from typing import Callable, Dict, Optional, Type

from munch import Munch

from ..processors import (
    DAG,
    DAGFlattener,
    Data,
    FlatDAG,
    InputPortAddress,
    InputPortName,
    NodeName,
    Output,
    OutputPortAddress,
    OutputPortName,
    Processor,
    RunContext,
    processor,
)
from .utils import find_downstream_nodes_for_input_ports


@processor
class _ValueCaptureProcessor:
    """Processor that holds a value provided at construct time, and outputs that value.

    For use by Estimator.
    """

    def __init__(self, value_type: Type, value: Data):
        self._value_type = value_type
        self.value = value

    def get_input_schema(self) -> Dict[InputPortName, Type[Data]]:
        return dict()

    def get_output_schema(self) -> Dict[OutputPortName, Type[Data]]:
        return dict(value=self._value_type)

    def process(self, run_context: RunContext) -> Dict[OutputPortName, Data]:
        return Munch(value=self.value)


@processor
class PersistSubgraphForInputPorts:
    """Processor for persisting a subgraph of a DAG.

    For use by Estimator.
    """

    def __init__(self, flat_dag: FlatDAG, port_rename: Callable[[str], Optional[str]]):
        def input_port_filter(port_name: str) -> bool:
            return port_rename(port_name) is not None

        multiplex_nodes = find_downstream_nodes_for_input_ports(flat_dag, input_port_filter)
        input_schema = dict()
        addresses_to_capture = dict()
        nodes = dict()
        for node_name in multiplex_nodes:
            nodes[node_name] = flat_dag.nodes[node_name]
        input_edges = dict()
        for input_port_address, input_port_name in flat_dag.input_edges.items():
            if input_port_address.node in multiplex_nodes:
                input_edges[input_port_address] = port_rename(input_port_name)
        edges = dict()
        for input_port_address, output_port_address in flat_dag.edges.items():
            if input_port_address.node in multiplex_nodes:
                if output_port_address.node in multiplex_nodes:
                    edges[input_port_address] = output_port_address
                else:
                    input_schema[self._get_port_name(output_port_address)] = flat_dag.nodes[
                        output_port_address.node
                    ].get_output_schema()[output_port_address.port]
                    addresses_to_capture[output_port_address] = self._get_port_name(
                        output_port_address
                    )
                    edges[input_port_address] = OutputPortAddress(
                        self._get_value_capture_node_name(output_port_address), "value"
                    )
        output_edges = dict()
        for output_port_name, output_port_address in flat_dag.output_edges.items():
            if output_port_address.node in multiplex_nodes:
                output_edges[port_rename(output_port_name)] = output_port_address
        self.addresses_to_capture = addresses_to_capture
        self._input_schema = input_schema
        self._nodes = nodes
        self._input_edges = input_edges
        self._edges = edges
        self._output_edges = output_edges

    def _get_value_capture_node_name(self, output_port_address: OutputPortAddress) -> NodeName:
        return NodeName(output_port_address.node) + NodeName(output_port_address.port)

    def _get_port_name(self, output_port_address: OutputPortAddress) -> InputPortName:
        return InputPortName(
            output_port_address.node.replace("/", "_") + f"_{output_port_address.port}"
        )

    def get_input_schema(self) -> Dict[InputPortName, Type[Data]]:
        return self._input_schema

    def get_output_schema(self) -> Dict[OutputPortName, Type[Data]]:
        return dict(processor=Processor)

    def process(self, run_context: RunContext, **inputs: Data) -> Output(processor=Processor):
        nodes = self._nodes.copy()
        for output_port_address, input_port_name in self.addresses_to_capture.items():
            value = inputs[input_port_name]
            value_capture_node_name = self._get_value_capture_node_name(output_port_address)
            value_capture_node = _ValueCaptureProcessor(self._input_schema[input_port_name], value)
            nodes[value_capture_node_name] = value_capture_node
        flat_dag = FlatDAG(
            nodes=nodes,
            input_edges=self._input_edges,
            edges=self._edges,
            output_edges=self._output_edges,
        )
        dag_flattener = DAGFlattener()
        dag = dag_flattener.unflatten(flat_dag)
        return Munch(processor=dag)


class Estimator(DAG):
    """A TrainAndPredict pipeline that outputs a DAG encoding the trained prediction pipeline.

    Args:
        train_and_predict: a DAG with two sets of input ports and two sets of output ports
        * train input/output ports whose names start with "train_"
        * holdout input/output ports whose names start with "holdout_"
        train output ports are not allowed to be downstream from holdout input ports.

    The Estimator would hold a copy of the given train_and_predict DAG, with an additional node
    that creates a predictor DAG at run time, outputed from the "predictor" output port of the
    Estimator.  The predictor DAG captures the trained values and is guaranteed to be functionally
    equivalent to the holdout predict path of the given train_and_predict.

    """

    def __init__(self, train_and_predict: Processor):
        def rename_holdout_port(port_name: str) -> str:
            if port_name.startswith("holdout_"):
                l = len("holdout_")
                return port_name[l:]
            else:
                return None

        dag_flattener = DAGFlattener()
        flat_estimator = dag_flattener.flatten(train_and_predict)
        persister = PersistSubgraphForInputPorts(flat_estimator, rename_holdout_port)
        nodes = flat_estimator.nodes.copy()
        input_edges = flat_estimator.input_edges.copy()
        edges = flat_estimator.edges.copy()
        output_edges = flat_estimator.output_edges.copy()
        nodes["produce_predictor"] = persister
        for output_port_address, input_port_name in persister.addresses_to_capture.items():
            edges[InputPortAddress("produce_predictor", input_port_name)] = output_port_address
        output_edges["predictor"] = OutputPortAddress("produce_predictor", "processor")
        flat_estimator = FlatDAG(
            nodes=nodes, input_edges=input_edges, edges=edges, output_edges=output_edges
        )
        estimator = dag_flattener.unflatten(flat_estimator)
        super().__init__(
            nodes=estimator.nodes,
            input_edges=estimator.input_edges,
            edges=estimator.edges,
            output_edges=estimator.output_edges,
        )
