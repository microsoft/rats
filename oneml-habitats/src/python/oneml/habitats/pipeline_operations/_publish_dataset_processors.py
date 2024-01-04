from typing import Mapping

from oneml.processors.dag import IProcess
from oneml.processors.utils import frozendict

from ._datasets import (
    DatasetPrepareOutput,
    DatasetPublishOutput,
    DatasetPublishSpecifications,
    IDatasetPrepareAndPublishService,
)


class PrepareOutputDatasetProcessor(IProcess):
    _dataset_prepare_and_publish: IDatasetPrepareAndPublishService

    def __init__(
        self,
        dataset_prepare_and_publish: IDatasetPrepareAndPublishService,
    ) -> None:
        self._dataset_prepare_and_publish = dataset_prepare_and_publish

    def process(
        self,
        output_base_uri: str,
        allow_overwrite: bool,
        input_uris: Mapping[str, str] = frozendict(),
    ) -> DatasetPrepareOutput:
        return self._dataset_prepare_and_publish.prepare(
            input_uris=input_uris,
            output_base_uri=output_base_uri,
            allow_overwrite=allow_overwrite,
        )


class PublishOutputDatasetProcessor(IProcess):
    _dataset_prepare_and_publish: IDatasetPrepareAndPublishService

    def __init__(
        self,
        dataset_prepare_and_publish: IDatasetPrepareAndPublishService,
    ) -> None:
        self._dataset_prepare_and_publish = dataset_prepare_and_publish

    def process(
        self,
        resolved_output_base_uri: str,
        resolved_output_uris: Mapping[str, str],
        output_base_path_within_dataset: str | None,
        dataset_publish_specifications: DatasetPublishSpecifications | None,
    ) -> DatasetPublishOutput:
        return self._dataset_prepare_and_publish.publish(
            resolved_output_base_uri=resolved_output_base_uri,
            resolved_output_uris=resolved_output_uris,
            output_base_path_within_dataset=output_base_path_within_dataset,
            dataset_publish_specifications=dataset_publish_specifications,
        )
