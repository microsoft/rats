from typing import Optional, Sequence, Tuple

from .._frozendict import frozendict
from .._orderedset import oset
from .._ux import Workflow, WorkflowClient


class ScatterGatherBuilders:
    """Builders for workflows that follow a scatter-process-gather pattern."""

    @classmethod
    def build(
        cls, name: str, scatter: Workflow, process_batch: Workflow, gather: Workflow
    ) -> Workflow:
        """
        Args:
            name: name for the built workflow.
            scatter: a workflow that takes inputs and splits them into K batches.
            process_batch: a workflow to be applied to each batch.
            gather: a workflow that takes K batches of inputs and combines them.

        Scatter output names are expected to correspond to process_batch input names as follows:
        * Each output name of scatter should be composed of an input name of gather followed by a
          serial number, potentially sperated by an underscore.
        * The serial numbers form the batch ids.  The set of batch ids should be identical fro all
          outputs of scatter.

        The inputs of scatter become inputs of the ScatterGather workflow.
        The outputs of gather become outputs of the ScatterGather workflow.

        Each input name of process_batch can be:
        * A prefix of scatter output names as explained above.  For each batch, the value for that
          input will come from the corresponding output of scatter.
        * Not a prefix of scatter output names.  In this case it is assumed to be
          batch-independent.  It will become an input of the ScatterGather workflow, and all
          batches will receive the same value for that input.

        For every output name A of process_batch, gather should either have
            * an input named A that accepts multiple dependencies (*arg)
            or
            * K input names composed of the A followed by a batch key.
        """
        (
            batch_keys,
            batch_input_and_batch_key_to_scatter_output,
        ) = cls._get_batch_input_and_batch_key_to_scatter_output(
            oset(scatter.ret), oset(process_batch.sig)
        )
        batch_output_and_batch_key_to_gather_input = (
            cls._get_batch_output_and_batch_key_to_gather_input(
                batch_keys, oset(process_batch.ret), oset(gather.sig)
            )
        )
        batch_workflows = frozendict[int, Workflow](
            {
                batch_key: WorkflowClient.compose_workflow(
                    cls._get_batch_workflow_name(batch_key), (process_batch,), ()
                )
                for batch_key in batch_keys
            }
        )
        w = WorkflowClient.compose_workflow(
            name,
            workflows=(scatter, gather) + tuple(batch_workflows.values()),
            dependencies=(
                tuple(
                    (
                        scatter.ret[
                            batch_input_and_batch_key_to_scatter_output[port_name][batch_key]
                        ]
                        >> batch_workflows[batch_key].sig[port_name]
                    )
                    for port_name in batch_input_and_batch_key_to_scatter_output
                    for batch_key in batch_keys
                )
                + tuple(
                    (
                        batch_workflows[batch_key].ret[port_name]
                        >> gather.sig[gather_port_mapping[batch_key]]
                    )
                    for port_name, gather_port_mapping in (
                        batch_output_and_batch_key_to_gather_input.items()
                    )
                    for batch_key in batch_keys
                )
            ),
            input_dependencies=(
                tuple(port_name >> scatter.sig[port_name] for port_name in scatter.sig)
                + tuple(
                    port_name >> batch_workflows[batch_key].sig[port_name]
                    for port_name in process_batch.sig
                    if port_name not in batch_input_and_batch_key_to_scatter_output
                    for batch_key in batch_keys
                )
            ),
            output_dependencies=tuple(
                gather.ret[port_name] >> port_name for port_name in gather.ret
            ),
        )
        return w

    @classmethod
    def _get_batch_workflow_name(cls, batch_key: int) -> str:
        return f"batch_{batch_key:03d}"

    @classmethod
    def _parse_batch_key(cls, batch_input: str, scatter_output: str) -> int:
        suffix = scatter_output[len(batch_input) :]
        if suffix.startswith("_"):
            suffix = suffix[1:]
        try:
            batch_key = int(suffix)
        except ValueError:
            raise ValueError(
                "Expected scatter output names to be composed of process_batch input names and an "
                f"integer.  Scatter output <{scatter_output}> starts with batch input "
                f"<{batch_input}> but the suffix is not an integer."
            )
        return batch_key

    @classmethod
    def _get_batch_input_and_batch_key_to_scatter_output(
        cls, scatter_outputs: oset[str], batch_inputs: oset[str]
    ) -> Tuple[Sequence[int], frozendict[str, frozendict[int, str]]]:
        batch_inputs_by_length_downwards = sorted(batch_inputs, key=lambda s: len(s), reverse=True)
        batch_keys: Optional[oset[int]] = None
        batch_input_and_batch_key_to_scatter_output: dict[str, frozendict[int, str]] = dict()
        for batch_input in batch_inputs_by_length_downwards:
            matching_scatter_outputs = [
                scatter_output
                for scatter_output in scatter_outputs
                if scatter_output.startswith(batch_input)
            ]
            if len(matching_scatter_outputs) > 0:
                batch_keys_mapping = frozendict[int, str](
                    {
                        cls._parse_batch_key(batch_input, scatter_output): scatter_output
                        for scatter_output in matching_scatter_outputs
                    }
                )
                matching_batch_keys = oset(batch_keys_mapping)
                if batch_keys is None:
                    batch_keys = matching_batch_keys
                else:
                    assert batch_keys == matching_batch_keys
                batch_input_and_batch_key_to_scatter_output[batch_input] = batch_keys_mapping
        if batch_keys is None:
            batch_keys = oset()
        return sorted(batch_keys), frozendict(batch_input_and_batch_key_to_scatter_output)

    @classmethod
    def _get_batch_output_and_batch_key_to_gather_input(
        cls,
        batch_keys: Sequence[int],
        batch_outputs: oset[str],
        gather_inputs: oset[str],
    ) -> frozendict[str, frozendict[int, str]]:
        def get_mapper_for_port(port_name: str) -> frozendict[int, str]:
            if port_name in gather_inputs:
                return frozendict[int, str]({batch_key: port_name for batch_key in batch_keys})
            else:
                batch_keys_mapping = frozendict[int, str](
                    {
                        cls._parse_batch_key(port_name, gather_input): gather_input
                        for gather_input in gather_inputs
                        if gather_input.startswith(port_name)
                    }
                )
                matching_batch_keys = oset(batch_keys_mapping)
                assert oset(batch_keys) == matching_batch_keys
                return batch_keys_mapping

        return frozendict(
            {port_name: get_mapper_for_port(port_name) for port_name in batch_outputs}
        )
