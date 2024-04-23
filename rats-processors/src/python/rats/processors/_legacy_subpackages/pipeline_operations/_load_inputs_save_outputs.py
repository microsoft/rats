from typing import Any, Literal

from rats.processors._legacy_subpackages.io import (
    IReadFromUriPipelineBuilder,
    IWriteToNodeBasedUriPipelineBuilder,
)
from rats.processors._legacy_subpackages.ux import (
    InPort,
    OutPort,
    UPipeline,
    UPipelineBuilder,
    ensure_non_clashing_pipeline_names,
)


class LoadInputsSaveOutputs:
    _read_from_uri: IReadFromUriPipelineBuilder
    _write_to_node_based_uri: IWriteToNodeBasedUriPipelineBuilder

    def __init__(
        self,
        read_from_uri: IReadFromUriPipelineBuilder,
        write_to_node_based_uri: IWriteToNodeBasedUriPipelineBuilder,
    ):
        self._read_from_uri = read_from_uri
        self._write_to_node_based_uri = write_to_node_based_uri

    def _get_data_type(
        self, entry: InPort[Any] | OutPort[Any], name: str, kind: Literal["Input", "Output"]
    ) -> type:
        parameter = entry[0]
        processor_param = parameter.param
        annotation = processor_param.annotation
        if not isinstance(annotation, type):
            raise ValueError(f"{kind} {name} has non-type annotation {annotation}.")
        return annotation

    def _get_load_pipeline(self, pipeline: UPipeline) -> UPipeline:
        entry_loaders = tuple(
            (
                self._read_from_uri.build(self._get_data_type(entry, entry_name, "Input"))
                .decorate(entry_name)
                .rename_inputs({"uri": f"input_uris.{entry_name}"})
                .rename_outputs({"data": f"inputs.{entry_name}"})
                for entry_name, entry in pipeline.inputs.inputs_to_load._asdict().items()
            )
        )
        pl = UPipelineBuilder.combine(
            entry_loaders,
            name="load_inputs",
        )
        if pl.name == pipeline.name:
            pl = pl.decorate("_" + pl.name)
        return pl

    def _get_save_pipeline(self, pipeline: UPipeline) -> UPipeline:
        entry_savers = tuple(
            (
                self._write_to_node_based_uri.build(
                    data_type=self._get_data_type(entry, entry_name, "Output")
                )
                .decorate(entry_name)
                .rename_inputs({"data": f"outputs.{entry_name}"})
                .rename_outputs({"uri": f"output_uris.{entry_name}"})
                for entry_name, entry in pipeline.outputs.outputs_to_save._asdict().items()
            )
        )
        pl = UPipelineBuilder.combine(
            entry_savers,
            name="save_outputs",
        )
        if pl.name == pipeline.name:
            pl = pl.decorate("_" + pl.name)
        return pl

    def _add_load_and_save(self, pipeline: UPipeline) -> UPipeline:
        pipelines: tuple[UPipeline, ...] = (pipeline,)
        dependencies = tuple()
        if "inputs_to_load" in pipeline.inputs:
            load_pipeline = self._get_load_pipeline(pipeline)
            pipelines = (*pipelines, load_pipeline)
            dependencies = (
                *dependencies,
                load_pipeline.outputs.inputs >> pipeline.inputs.inputs_to_load,
            )
        if "outputs_to_save" in pipeline.outputs:
            save_pipeline = self._get_save_pipeline(pipeline)
            pipelines = (*pipelines, save_pipeline)
            dependencies = (
                *dependencies,
                pipeline.outputs.outputs_to_save >> save_pipeline.inputs.outputs,
            )
        if len(pipelines) == 1:
            return pipeline
        else:
            pipelines = tuple(ensure_non_clashing_pipeline_names(*pipelines))

            pl = UPipelineBuilder.combine(
                pipelines,
                name=pipeline.name,
                dependencies=dependencies,
            )
            return pl

    def __call__(self, pipeline: UPipeline) -> UPipeline:
        """Add load and save nodes to the given pipeline.

        If the pipeline has an `inputs_to_load` in_collection, then a an `input_uris`
        in_collection, with the same set of entry names will replace it.  At run time, each input
        expected by `inputs_to_load` will be loaded from the corresponding uri.

        If the pipeline has an `outputs_to_save` out_collection, then an `output_uris`
        out_collection, with the same set of entry names will replace it, and an `output_base_uri`
        input will be added.  At run time, each output exposed by `outputs_to_save` will be saved
        to a uri under the `output_base_uri` folder.  The uri used to save each output will be
        exposed as an `output_uris` entry.
        """
        return self._add_load_and_save(pipeline)
