from typing import Sequence

from oneml.habitats.pipeline_operations._datasets import IDatasetPrepareAndPublishService
from oneml.processors.pipeline_operations import CollectionToDict, DictToCollection
from oneml.processors.utils import frozendict
from oneml.processors.ux import UPipeline, UPipelineBuilder
from oneml.services import ServiceId

from ._publish_dataset_processors import (
    PrepareOutputDatasetProcessor,
    PublishOutputDatasetProcessor,
)


class PublishOutputsAsDataset:
    _collection_to_dict: CollectionToDict
    _dict_to_collection: DictToCollection
    _dataset_prepare_and_publish_service_id: ServiceId[IDatasetPrepareAndPublishService]

    def __init__(
        self,
        collection_to_dict: CollectionToDict,
        dict_to_collection: DictToCollection,
        dataset_prepare_and_publish_service_id: ServiceId[IDatasetPrepareAndPublishService],
    ) -> None:
        self._collection_to_dict = collection_to_dict
        self._dict_to_collection = dict_to_collection
        self._dataset_prepare_and_publish_service_id = dataset_prepare_and_publish_service_id

    def _prepare_with_inputs(self, inputs: Sequence[str]) -> UPipeline:
        c2d = self._collection_to_dict(
            entries=inputs,
            element_type=str,
        )
        pl: UPipeline = UPipelineBuilder.task(
            processor_type=PrepareOutputDatasetProcessor,
            services=frozendict(
                dataset_prepare_and_publish=self._dataset_prepare_and_publish_service_id
            ),
        )
        d2c = self._dict_to_collection(
            entries=inputs,
            element_type=str,
        )
        pl = (
            UPipelineBuilder.combine(
                name="prepare_output_dataset",
                pipelines=[c2d, pl, d2c],
                dependencies=(
                    c2d.outputs.dct >> pl.inputs.input_uris,
                    pl.outputs.resolved_input_uris >> d2c.inputs.dct,
                ),
            )
            .rename_inputs(dict(col="input_uris"))
            .rename_outputs(dict(col="resolved_input_uris"))
        )
        return pl

    def _prepare_without_inputs(self) -> UPipeline:
        pl: UPipeline = UPipelineBuilder.task(
            processor_type=PrepareOutputDatasetProcessor,
            services=frozendict(
                dataset_prepare_and_publish=self._dataset_prepare_and_publish_service_id
            ),
        )
        pl = UPipelineBuilder.combine(
            name="prepare_output_dataset",
            pipelines=[pl],
            inputs={k: pl.inputs[k] for k in pl.inputs if k != "input_uris"},
            outputs={k: pl.outputs[k] for k in pl.outputs if k != "resolved_input_uris"},
        )
        return pl

    def _publish(self, outputs: Sequence[str]) -> UPipeline:
        c2d = self._collection_to_dict(
            entries=outputs,
            element_type=str,
        )
        pl: UPipeline = UPipelineBuilder.task(
            name="publish_output_dataset",
            processor_type=PublishOutputDatasetProcessor,
            services=frozendict(
                dataset_prepare_and_publish=self._dataset_prepare_and_publish_service_id
            ),
        )
        d2c = self._dict_to_collection(
            entries=outputs,
            element_type=str,
        )
        pl = (
            UPipelineBuilder.combine(
                pipelines=[c2d, pl, d2c],
                name="publish_output_dataset",
                dependencies=(
                    c2d.outputs.dct >> pl.inputs.resolved_output_uris,
                    pl.outputs.output_uris >> d2c.inputs.dct,
                ),
            )
            .rename_inputs(dict(col="resolved_output_uris"))
            .rename_outputs(dict(col="output_uris"))
        )
        return pl

    def publish_outputs_as_dataset_provider(self, pipeline: UPipeline) -> UPipeline:
        if "output_base_uri" not in pipeline.inputs:
            raise ValueError("pipeline must have output_base_uri input")

        if "input_uris" in pipeline.inputs:
            prepare = self._prepare_with_inputs(list(pipeline.inputs.input_uris))
        else:
            prepare = self._prepare_without_inputs()

        publish = self._publish(list(pipeline.outputs.output_uris))
        if pipeline.name in (prepare.name, publish.name):
            pipeline = pipeline.decorate("_" + pipeline.name)

        pl = UPipelineBuilder.combine(
            pipelines=[prepare, pipeline, publish],
            name=pipeline.name,
            dependencies=(
                prepare.outputs.resolved_output_base_uri >> pipeline.inputs.output_base_uri,
                prepare.outputs.resolved_output_base_uri
                >> publish.inputs.resolved_output_base_uri,
                prepare.outputs.output_base_path_within_dataset
                >> publish.inputs.output_base_path_within_dataset,
                prepare.outputs.dataset_publish_specifications
                >> publish.inputs.dataset_publish_specifications,
                pipeline.outputs.output_uris >> publish.inputs.resolved_output_uris,
            )
            + (
                (prepare.outputs.resolved_input_uris >> pipeline.inputs.input_uris,)
                if "input_uris" in pipeline.inputs
                else tuple()
            ),
        )
        return pl

    def __call__(self, pipeline: UPipeline) -> UPipeline:
        """Add dataset publishing to pipeline that already handles load and save from uris.

        Args:
            pipeline: A pipeline that loads from uris and saves to a uri base folder.

        Expected pipeline inputs:
            output_base_uri: str
                    Whatever is saved to that location will become part of the published dataset.
                    Supported schemes should include file:// and abfss://.
            Optional pipeline inputs:
                input_uris: str
                    Locations from which the pipeline will read inputs.
                    Supported schemes should include file:// and abfss://.
            Expected pipeline outputs:
                output_uris: str
                    The locations under which the pipeline saved its outputs, expected to be under
                    output_base_uri.

        Returns:
            A pipeline wrapping the provided pipeline, adding support for ampds:// uris,
            representing datasets.

            The pipeline will expose identical inputs and outputs as the provided pipeline, with
            the addition of a new `allow_overrides` input, as explained below.

            If base_output_uri is not an ampds:// uri, then the behaviour will be identical to the
            provided pipeline.

            If it is an ampds:// uri, then:

            1. The outputs will be written into a new commit of the dataset (and partition and
                namespace) specified by the ampds:// uri.
            2. The `allow_overrides` input controls the behaviour if a commit already exists.  If
                true, it will be overridden by the new commit.  Otherwise an error will be raised.
            3. Any ampds:// uri in input_uris will be a parent commit of the published dataset.
            4. The output uris will be an ampds:// uri, fully specifying the created commit,
                pointing to the locations within the dataset where the outputs were saved.
        """
        return self.publish_outputs_as_dataset_provider(pipeline)
