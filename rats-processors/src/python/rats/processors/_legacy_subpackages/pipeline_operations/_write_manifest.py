from rats.processors._legacy_subpackages.io import IWriteToRelativePathPipelineBuilder
from rats.processors._legacy_subpackages.ux import UPipeline, UPipelineBuilder

from ._build_manifest_processor import BuildManifestProcessor, Manifest


class AddOutputManifest:
    _write_to_relative_path: IWriteToRelativePathPipelineBuilder

    def __init__(
        self,
        write_to_relative_path: IWriteToRelativePathPipelineBuilder,
    ):
        self._write_to_relative_path = write_to_relative_path

    def _write_manifest_provider(self, pipeline: UPipeline) -> UPipeline:
        input_annotation = {f"_{k}": str for k in pipeline.outputs.output_uris} | {
            "output_base_uri": str,
        }
        renames = {f"_{k}": f"output_uris.{k}" for k in pipeline.outputs.output_uris}
        build_manfiest = UPipelineBuilder.task(
            BuildManifestProcessor, input_annotation=input_annotation
        ).rename_inputs(renames)
        write_manifest = (
            self._write_to_relative_path.build(data_type=Manifest, relative_path="manifest.json")
            .rename_inputs({"data": "manifest"})
            .rename_outputs({"uri": "output_uris.manifest"})
        )
        pl = UPipelineBuilder.combine(
            [build_manfiest, write_manifest],
            name="add_output_manifest",
            dependencies=(build_manfiest.outputs.manifest >> write_manifest.inputs.manifest,),
        )
        if pl.name == pipeline.name:
            pl = pl.decorate("_" + pl.name)
        return pl

    def _provider(self, pipeline: UPipeline) -> UPipeline:
        write_manifest = self._write_manifest_provider(pipeline)
        pl = UPipelineBuilder.combine(
            [pipeline, write_manifest],
            name=pipeline.name,
            dependencies=(pipeline.outputs.output_uris >> write_manifest.inputs.output_uris,),
        )
        return pl

    def __call__(self, pipeline: UPipeline) -> UPipeline:
        """Add a manifest output to the pipeline.

        Args:
            pipeline: A pipeline that saves outputs to a uri base folder.

        Expected pipeline inputs:
            output_base_uri: str
                A folder uri to save the manifest to.
        Expected pipeline outputs:
            output_uris:
                A mapping of output names to locations where they were saved by the pipeline.

        A manifest.json will be written, directly under output_base_uri.  The manifest will contain
        a mapping of output names to paths to the output locations.  Locations that are under
        output_base_uri will be relative paths, otherwise they will be the original uris provided
        in the pipeline's output_uris collection.  Any existing manifest.json will be overwritten.

        The returned pipeline will have the same inputs, inputs, outputs, and
        outputs as the given pipeline, except the out_collection output_uris will contain
        a single entry, manifest, holding the uri of the saved manifest.json.
        """
        return self._provider(pipeline)
