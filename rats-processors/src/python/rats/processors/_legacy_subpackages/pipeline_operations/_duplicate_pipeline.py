from collections.abc import Sequence
from dataclasses import dataclass, field
from functools import reduce
from typing import Any

from omegaconf import MISSING

from rats.processors._legacy_subpackages.ux import PipelineConf, UPipeline, UPipelineBuilder


class DuplicatePipeline:
    """Builds a pipeline with multiple copies of a given pipeline.

    Simple inputs/outputs are converted to in/out collections, with the entry names corresponding
    to pipeline copy name.
    in/out collection entries are suffixed with pipeline copy name.

    inputs specified in broadcast_inputs are not duplicated, instead they are
    broadcasted to all copies.
    """

    @staticmethod
    def __call__(
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
                entry_name + ("." if entry_name.count(".") == 0 else "_") + copy_name: entry
                for copy_name, pipeline_copy in copies.items()
                for entry_name, entry in pipeline_copy.inputs._asdict().items()
                if entry_name not in broadcast_inputs
            },
            outputs={
                entry_name + ("." if entry_name.count(".") == 0 else "_") + copy_name: entry
                for copy_name, pipeline_copy in copies.items()
                for entry_name, entry in pipeline_copy.outputs._asdict().items()
            },
        )


@dataclass
class DuplicatePipelineConf(PipelineConf):
    _target_: str = "rats.processors._legacy_subpackages.pipeline_operations._duplicate_pipeline.DuplicatePipeline.__call__"
    pipeline: Any = MISSING
    copy_names: list[str] = MISSING
    broadcast_inputs: list[str] = field(default_factory=list)
