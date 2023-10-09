from functools import reduce
from typing import Sequence

from oneml.processors.ux import UPipeline, UPipelineBuilder


class DuplicatePipeline:
    """Builds a pipeline with mutiple copies of a given pipeline.

    Simple inputs/outputs are converted to in/out collections, with the entry names corresponding
    to pipeline copy name.
    in/out collection entries are prefixed with pipeline copy name.

    inputs/in_collections specified in broadcast_inputs are not duplicated, instead they are
    broadcasted to all copies.
    """

    def __call__(
        self,
        pipeline: UPipeline,
        copy_names: Sequence[str],
        broadcast_inputs: Sequence[str] = (),
    ) -> UPipeline:
        copies = {name: pipeline.decorate(name) for name in copy_names}
        return UPipelineBuilder.combine(
            pipelines=tuple(copies.values()),
            name=pipeline.name,
            inputs={
                entry_name: reduce(
                    lambda a, b: a | b,
                    (pipeline_copy.inputs[entry_name] for pipeline_copy in copies.values()),
                )
                for entry_name in pipeline.inputs
                if entry_name in broadcast_inputs
            }
            | {
                collection_name: reduce(
                    lambda a, b: a | b,
                    (
                        pipeline_copy.in_collections[collection_name]
                        for pipeline_copy in copies.values()
                    ),
                )
                for collection_name in pipeline.in_collections
                if collection_name in broadcast_inputs
            }
            | {
                entry_name + "." + copy_name: entry
                for copy_name, pipeline_copy in copies.items()
                for entry_name, entry in pipeline_copy.inputs._asdict().items()
                if entry_name not in broadcast_inputs
            }
            | {
                collection_name + "." + copy_name + "_" + entry_name: entry
                for copy_name, pipeline_copy in copies.items()
                for collection_name, collection in pipeline_copy.in_collections._asdict().items()
                for entry_name, entry in collection._asdict().items()
                if collection_name not in broadcast_inputs
            },
            outputs={
                entry_name + "." + copy_name: entry
                for copy_name, pipeline_copy in copies.items()
                for entry_name, entry in pipeline_copy.outputs._asdict().items()
            }
            | {
                collection_name + "." + copy_name + "_" + entry_name: entry
                for copy_name, pipeline_copy in copies.items()
                for collection_name, collection in pipeline_copy.out_collections._asdict().items()
                for entry_name, entry in collection._asdict().items()
            },
        )
