# type: ignore
# flake8: noqa
from typing import Sequence, Set, Tuple

from ..processors import DAG, InputPortAddress, OutputPortAddress, Processor


class ScatterGather(DAG):
    """A DAG following scatter-process-gather pattern.

    Args:
        scatter: a processor that take inputs and splits them into K batches.
        process_batch: a processor to be applied to each batch.
        gather: a processor that takes K batches of inputs and combines them.

    Inputs of scatter are inputs of the ScatterGather DAG.
    Outputs of gather are output of the ScatterGather DAG.

    Edges between the scatter node and the K process_batch nodes and from those to the gather node
    are computed by comparing the port names of the different nodes.

    For an input port name A of process_batch:
        If it is not a prefix of an output port name of scatter, it becomes a input of the
            ScatterGather DAG.
        If it is a prefix of K output port names of scatter, then the remaining suffixes of those
            output port names define batch keys.  It is verified that the set of batch keys defined
            by any other input port name B of process batch is identical.

    For an output port name A of process_batch, there should be K input port names of gather each
        composed of the output port name followed by a batch key.
    """

    def __init__(
        self,
        scatter: Processor,
        process_batch: Processor,
        gather: Processor,
    ):
        batch_keys, unmatched_batch_inputs = self._get_batch_keys(
            scatter.get_output_schema().keys(), process_batch.get_input_schema().keys()
        )
        nodes = dict()
        input_edges = dict()
        edges = dict()
        output_edges = dict()
        nodes["scatter"] = scatter
        for batch_key in batch_keys:
            nodes[f"batch{batch_key}"] = process_batch
        nodes["gather"] = gather
        for port_name in scatter.get_input_schema().keys():
            input_edges[InputPortAddress("scatter", port_name)] = port_name
        for port_name in process_batch.get_input_schema().keys():
            for batch_key in batch_keys:
                target_address = InputPortAddress(f"batch{batch_key}", port_name)
                if port_name in unmatched_batch_inputs:
                    input_edges[target_address] = port_name
                else:
                    edges[target_address] = OutputPortAddress("scatter", f"{port_name}{batch_key}")
        for port_name in process_batch.get_output_schema().keys():
            for batch_key in batch_keys:
                target_port_name = f"{port_name}{batch_key}"
                assert target_port_name in gather.get_input_schema().keys()
                edges[InputPortAddress("gather", target_port_name)] = OutputPortAddress(
                    f"batch{batch_key}", port_name
                )
        for port_name in gather.get_output_schema().keys():
            output_edges[port_name] = OutputPortAddress("gather", port_name)
        super().__init__(
            nodes=nodes, input_edges=input_edges, edges=edges, output_edges=output_edges
        )

    def _get_batch_keys(
        self, scatter_outputs: Set[str], batch_inputs: Set[str]
    ) -> Tuple[Sequence[str], Sequence[str]]:
        batch_inputs_by_length_downwards = sorted(batch_inputs, key=lambda s: len(s), reverse=True)
        batch_keys = None
        unmatched_batch_inputs = set()
        for batch_input in batch_inputs_by_length_downwards:
            matching_scatter_outputs = [
                scatter_output
                for scatter_output in scatter_outputs
                if scatter_output.startswith(batch_input)
            ]
            if len(matching_scatter_outputs) > 0:
                matching_batch_keys = set(
                    [
                        scatter_output[len(batch_input) :]
                        for scatter_output in matching_scatter_outputs
                    ]
                )
                if batch_keys is None:
                    batch_keys = matching_batch_keys
                else:
                    assert batch_keys == matching_batch_keys
            else:
                unmatched_batch_inputs.add(batch_input)
        return batch_keys, unmatched_batch_inputs
