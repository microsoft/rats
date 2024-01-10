from collections.abc import Sequence

from ..ux import InPorts, Inputs, OutPorts, Outputs, UPipeline, UPipelineBuilder


class ScatterGatherBuilders:
    """Builders for pipelines that follow a scatter-process-gather pattern."""

    @classmethod
    def build(
        cls, name: str, scatter: UPipeline, process_batch: UPipeline, gather: UPipeline
    ) -> UPipeline:
        """Builds a pipeline that follows a scatter-process-gather pattern.

        Args:
            name: name for the built pipeline.
            scatter: a pipeline that takes inputs and splits them into batches.
            process_batch: a pipeline to be applied to each batch.
            gather: a pipeline that takes K batches of inputs and combines them.

        batch identifiers: All out_collections of scatter and in_collections of gather should have
        the same set of entry names.  Those will be the batch identifiers.

        scatter should not have outputs (just out_collections).

        process_batch should not have in_collections or out_collections.

        All out_collections of scatter should have corresponding-by-name inputs in process_batch.
        All outputs of process_batch should have corresponding-by-name in_collections in gather.

        process_batch will be duplicated for each batch.

        scatter out_collection entries will be connected with the inputs of the corresponding copy
        of process_batch. outputs of each copy of process_batch will be connected with the entries
        of the corresponding in_collections of gather.

        The inputs of the built pipeline will be the inputs of scatter, the inputs of process_batch
        that do not correspond to out_collections of scatter, and the inputs of gather that do not
        correspond to out_collections of process_batch.
        The in_collections of the built pipeline will be the in_collections of scatter, and the
        in_collections of gather that do not correspond to outputs of process_batch.

        The outputs of the built pipeline will be the outputs of gather.
        """
        batch_keys = cls._get_batch_keys(scatter.outputs, gather.inputs)
        if any(o for o in scatter.outputs._asdict() if o.count(".") == 0):
            raise ValueError("scatter should not have single outputs.")
        if any(o for o in process_batch.inputs._asdict() if o.count(".")):
            raise ValueError("process_batch should not have in_collections.")
        if any(o for o in process_batch.outputs._asdict() if o.count(".")):
            raise ValueError("process_batch should not have out_collections.")
        if set(o for o in scatter.outputs._asdict() if o.count(".")) & set(
            o for o in process_batch.inputs._asdict() if o.count(".")
        ):
            raise ValueError(
                "All out_collections of scatter should have corresponding-by-name inputs in "
                + "process_batch."
            )
        input_cols = tuple(g for g in gather.inputs if isinstance(gather.inputs[g], InPorts))
        if process_batch.outputs - input_cols:
            raise ValueError(
                "All outputs of process_batch should have corresponding-by-name in_collections in "
                + "gather."
            )

        process_batch_copies = {
            batch_key: process_batch.decorate(batch_key) for batch_key in batch_keys
        }

        pl = UPipelineBuilder.combine(
            [scatter, *list(process_batch_copies.values()), gather],
            name=f"scatter_gather_{process_batch.name}",
            dependencies=(
                tuple(
                    (
                        scatter.outputs[name][batch_key]
                        >> process_batch_copies[batch_key].inputs[name]
                    )
                    for name in scatter.outputs
                    for batch_key in batch_keys
                )
                + tuple(
                    (
                        process_batch_copies[batch_key].outputs[name]
                        >> gather.inputs[name][batch_key]
                    )
                    for name in process_batch.outputs
                    for batch_key in batch_keys
                )
            ),
        )
        return pl

    @classmethod
    def _get_batch_keys(cls, scatter_outputs: Outputs, gather_inputs: Inputs) -> Sequence[str]:
        scatter_outcol: dict[str, frozenset[str]] = {
            n: frozenset(scatter_outputs[n])
            for n in scatter_outputs
            if isinstance(scatter_outputs[n], OutPorts)
        }
        gather_incol: dict[str, frozenset[str]] = {
            n: frozenset(gather_inputs[n])
            for n in gather_inputs
            if isinstance(gather_inputs[n], InPorts)
        }
        if not scatter_outcol:
            raise ValueError("scatter must have at least one out_collection.")
        if not gather_incol:
            raise ValueError("gather must have at least one in_collection.")
        ref_col_name, ref_batch_keys = scatter_outcol.popitem()
        for col_name, batch_keys in gather_incol.items():
            if batch_keys != ref_batch_keys:
                missing = ref_batch_keys - batch_keys
                extra = batch_keys - ref_batch_keys
                raise ValueError(
                    "All out_collections of scatter and in_collections of gather must have the "
                    + f"same set of entry names. scatter {col_name} has {missing} missing and "
                    + f"{extra} extra when compared with scatter {ref_col_name}."
                )
        for col_name, batch_keys in gather_incol.items():
            if batch_keys != ref_batch_keys:
                missing = ref_batch_keys - batch_keys
                extra = batch_keys - ref_batch_keys
                raise ValueError(
                    "All out_collections of scatter and in_collections of gather must have the "
                    + f"same set of entry names. gather {col_name} has {missing} missing and "
                    + f"{extra} extra when compared with scatter {ref_col_name}."
                )
        return sorted(ref_batch_keys)
