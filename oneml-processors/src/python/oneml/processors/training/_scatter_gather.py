from typing import Iterable, Mapping, Sequence

from ..ux._builder import UPipelineBuilder
from ..ux._pipeline import UPipeline


class ScatterGatherBuilders:
    """Builders for pipelines that follow a scatter-process-gather pattern."""

    @classmethod
    def build(
        cls, name: str, scatter: UPipeline, process_batch: UPipeline, gather: UPipeline
    ) -> UPipeline:
        """
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
        batch_keys = cls._get_batch_keys(
            scatter.out_collections._asdict(), gather.in_collections._asdict()
        )
        if len(scatter.outputs) > 0:
            raise ValueError("scatter should not have outputs.")
        if len(process_batch.in_collections) > 0:
            raise ValueError("process_batch should not have in_collections.")
        if len(process_batch.out_collections) > 0:
            raise ValueError("process_batch should not have out_collections.")
        if len(frozenset(scatter.out_collections) - frozenset(process_batch.inputs)) > 0:
            raise ValueError(
                "All out_collections of scatter should have corresponding-by-name inputs in "
                "process_batch."
            )
        if len(frozenset(process_batch.outputs) - frozenset(gather.in_collections)) > 0:
            raise ValueError(
                "All outputs of process_batch should have corresponding-by-name in_collections in "
                "gather."
            )

        process_batch_copies = {
            batch_key: process_batch.decorate(batch_key) for batch_key in batch_keys
        }

        pl = UPipelineBuilder.combine(
            [scatter] + list(process_batch_copies.values()) + [gather],
            name=f"scatter_gather_{process_batch.name}",
            dependencies=(
                tuple(
                    (
                        scatter.out_collections[name][batch_key]
                        >> process_batch_copies[batch_key].inputs[name]
                    )
                    for name in scatter.out_collections
                    for batch_key in batch_keys
                )
                + tuple(
                    (
                        process_batch_copies[batch_key].outputs[name]
                        >> gather.in_collections[name][batch_key]
                    )
                    for name in process_batch.outputs
                    for batch_key in batch_keys
                )
            ),
        )
        return pl

    @classmethod
    def _get_batch_keys(
        cls,
        scatter_out_collections: Mapping[str, Iterable[str]],
        gather_in_collections: Mapping[str, Iterable[str]],
    ) -> Sequence[str]:
        if len(scatter_out_collections) == 0:
            raise ValueError("scatter must have at least one out_collection.")
        if len(gather_in_collections) == 0:
            raise ValueError("gather must have at least one in_collection.")
        scatter_batch_key_sets = {
            col_name: frozenset(v) for col_name, v in scatter_out_collections.items()
        }
        gather_batch_key_sets = {
            col_name: frozenset(v) for col_name, v in gather_in_collections.items()
        }
        ref_col_name, ref_batch_keys = scatter_batch_key_sets.popitem()
        for col_name, batch_keys in scatter_batch_key_sets.items():
            if batch_keys != ref_batch_keys:
                missing = ref_batch_keys - batch_keys
                extra = batch_keys - ref_batch_keys
                raise ValueError(
                    "All out_collections of scatter and in_collections of gather must have the "
                    f"same set of entry names. scatter {col_name} has {missing} missing and "
                    f"{extra} extra when compared with scatter {ref_col_name}."
                )
        for col_name, batch_keys in gather_batch_key_sets.items():
            if batch_keys != ref_batch_keys:
                missing = ref_batch_keys - batch_keys
                extra = batch_keys - ref_batch_keys
                raise ValueError(
                    "All out_collections of scatter and in_collections of gather must have the "
                    f"same set of entry names. gather {col_name} has {missing} missing and "
                    f"{extra} extra when compared with scatter {ref_col_name}."
                )
        return sorted(ref_batch_keys)
