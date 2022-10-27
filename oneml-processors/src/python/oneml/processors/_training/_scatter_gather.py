from typing import Set, Tuple

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
            scatter: a workflow that take inputs and splits them into K batches.
            process_batch: a workflow to be applied to each batch.
            gather: a workflow that takes K batches of inputs and combines them.

        The inputs of scatter become inputs of the ScatterGather workflow.
        The outputs of gather become outputs of the ScatterGather workflow.

        Dependencies between the scatter workflow and the K process_batch workflows and from those
        to the gather workflow are computed by comparing the input/output names of the different
        workflows.

        For an input name A of process_batch:
            If it is not a prefix of an output name of scatter, it becomes a input of the
                ScatterGather workflow.
            If it is a prefix of K output port names of scatter, then the remaining suffixes of
                those output names define batch keys.  The builder verifies that the set of batch
                keys defined by any other input name B of process batch is identical.

        For an output name A of process_batch, there should be K input names of gather each
            composed of the A followed by a batch key.
        """
        batch_keys, unmatched_batch_inputs = cls._get_batch_keys(
            frozenset(scatter.ret), frozenset(process_batch.sig)
        )
        batch_workflows = {
            batch_key: WorkflowClient.compose_workflow(f"batch{batch_key}", (process_batch,), ())
            for batch_key in batch_keys
        }
        w = WorkflowClient.compose_workflow(
            name,
            workflows=(scatter, gather) + tuple(batch_workflows.values()),
            dependencies=(
                tuple(
                    (
                        scatter.ret[f"{port_name}{batch_key}"]
                        >> batch_workflows[batch_key].sig[port_name]
                    )
                    for batch_key in batch_keys
                    for port_name in process_batch.sig
                    if port_name not in unmatched_batch_inputs
                )
                + tuple(
                    (
                        batch_workflows[batch_key].ret[port_name]
                        >> gather.sig[f"{port_name}{batch_key}"]
                    )
                    for batch_key in batch_keys
                    for port_name in process_batch.ret
                )
            ),
            input_dependencies=(
                tuple(port_name >> scatter.sig[port_name] for port_name in scatter.sig)
                + tuple(
                    port_name >> batch_workflows[batch_key].sig[port_name]
                    for batch_key in batch_keys
                    for port_name in unmatched_batch_inputs
                )
            ),
            output_dependencies=tuple(
                gather.ret[port_name] >> port_name for port_name in gather.ret
            ),
        )
        return w

    @classmethod
    def _get_batch_keys(
        cls, scatter_outputs: frozenset[str], batch_inputs: frozenset[str]
    ) -> Tuple[Set[str], Set[str]]:
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
        if batch_keys is None:
            batch_keys = set()
        return batch_keys, unmatched_batch_inputs
