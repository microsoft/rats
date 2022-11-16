from collections import ChainMap
from typing import Optional, Sequence, Tuple

from ..utils._frozendict import frozendict
from ..utils._orderedset import oset
from ..ux._client import PipelineBuilder
from ..ux._pipeline import Pipeline


class ScatterGatherBuilders:
    """Builders for pipelines that follow a scatter-process-gather pattern."""

    @classmethod
    def build(
        cls, name: str, scatter: Pipeline, process_batch: Pipeline, gather: Pipeline
    ) -> Pipeline:
        """
        Args:
            name: name for the built pipeline.
            scatter: a pipeline that takes inputs and splits them into K batches.
            process_batch: a pipeline to be applied to each batch.
            gather: a pipeline that takes K batches of inputs and combines them.

        Scatter outputs names are expected to correspond to process_batch inputs names as follows:
        * Each outputs name of scatter should be composed of an inputs name of gather followed by a
          serial number, potentially sperated by an underscore.
        * The serial numbers form the batch ids.  The set of batch ids should be identical fro all
          outputs of scatter.

        The inputs of scatter become inputs of the ScatterGather pipeline.
        The outputs of gather become outputs of the ScatterGather pipeline.

        Each inputs name of process_batch can be:
        * A prefix of scatter outputs names as explained above.  For each batch, the value for that
          inputs will come from the corresponding outputs of scatter.
        * Not a prefix of scatter outputs names.  In this case it is assumed to be
          batch-independent.  It will become an inputs of the ScatterGather pipeline, and all
          batches will receive the same value for that inputs.

        For every outputs name A of process_batch, gather should either have
            * an inputs named A that accepts multiple dependencies (*arg)
            or
            * K inputs names composed of the A followed by a batch key.
        """
        (
            batch_keys,
            batch_input_and_batch_key_to_scatter_output,
        ) = cls._get_batch_input_and_batch_key_to_scatter_output(
            oset(scatter.outputs), oset(process_batch.inputs)
        )
        batch_output_and_batch_key_to_gather_input = (
            cls._get_batch_output_and_batch_key_to_gather_input(
                batch_keys, oset(process_batch.outputs), oset(gather.inputs)
            )
        )
        batch_pipelines = frozendict[int, Pipeline](
            {
                batch_key: PipelineBuilder.combine(
                    process_batch, name=cls._get_batch_pipeline_name(batch_key)
                )
                for batch_key in batch_keys
            }
        )
        w = PipelineBuilder.combine(
            scatter,
            gather,
            *batch_pipelines.values(),
            name=name,
            dependencies=(
                tuple(
                    (
                        scatter.outputs[
                            batch_input_and_batch_key_to_scatter_output[port_name][batch_key]
                        ]
                        >> batch_pipelines[batch_key].inputs[port_name]
                    )
                    for port_name in batch_input_and_batch_key_to_scatter_output
                    for batch_key in batch_keys
                )
                + tuple(
                    (
                        batch_pipelines[batch_key].outputs[port_name]
                        >> gather.inputs[gather_port_mapping[batch_key]]
                    )
                    for port_name, gather_port_mapping in (
                        batch_output_and_batch_key_to_gather_input.items()
                    )
                    for batch_key in batch_keys
                )
            ),
            inputs=(
                ChainMap(
                    {port_name: scatter.inputs[port_name] for port_name in scatter.inputs},
                    {
                        port_name
                        + f".n{batch_key}": batch_pipelines[batch_key].inputs[port_name][
                            "batch_process"
                        ]
                        for port_name in process_batch.inputs
                        if port_name not in batch_input_and_batch_key_to_scatter_output
                        for batch_key in batch_keys
                    },
                )
            ),
            outputs={port_name: gather.outputs[port_name] for port_name in gather.outputs},
        )
        return w

    @classmethod
    def _get_batch_pipeline_name(cls, batch_key: int) -> str:
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
                "Expected scatter outputs names to be composed of process_batch inputs names and an "
                f"integer.  Scatter outputs <{scatter_output}> starts with batch inputs "
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
                    assert set(batch_keys) == set(matching_batch_keys)
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
