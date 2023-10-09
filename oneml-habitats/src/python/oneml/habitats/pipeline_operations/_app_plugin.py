import logging

from oneml.app import AppPlugin
from oneml.processors.pipeline_operations import (
    ITransformPipeline,
    OnemlProcessorsPipelineOperationsServices,
)
from oneml.services import (
    IManageServices,
    IProvideServices,
    ServiceId,
    scoped_service_ids,
    service_provider,
)

from ._datasets import OnemlHabitatsDatasetsPlugin, OnemlHabitatsDatasetsServices
from ._publish_outputs_as_dataset import PublishOutputsAsDataset

logger = logging.getLogger(__name__)


@scoped_service_ids
class _PrivateServices:
    PUBLISH_OUTPUTS_AS_DATASET = ServiceId[ITransformPipeline]("publish-outputs-as-dataset")


class OnemlHabitatsPipelineOperationsDiContainer:
    _app: IProvideServices

    def __init__(self, app: IProvideServices) -> None:
        self._app = app

    @service_provider(_PrivateServices.PUBLISH_OUTPUTS_AS_DATASET)
    def _publish_outputs_as_dataset(self) -> ITransformPipeline:
        return PublishOutputsAsDataset(
            collection_to_dict=self._app.get_service(
                OnemlProcessorsPipelineOperationsServices.COLLECTION_TO_DICT
            ),
            dict_to_collection=self._app.get_service(
                OnemlProcessorsPipelineOperationsServices.DICT_TO_COLLECTION
            ),
            dataset_prepare_and_publish_service_id=(
                OnemlHabitatsDatasetsServices.DATASET_PREPARE_AND_PUBLISH
            ),
        )


class OnemlHabitatsPipelineOperationsPlugin(AppPlugin):
    def load_plugin(self, app: IManageServices) -> None:
        logger.debug("initializing oneml-habitats-pipeline-operations plugin")
        app.parse_service_container(OnemlHabitatsPipelineOperationsDiContainer(app))

        OnemlHabitatsDatasetsPlugin().load_plugin(app)


class OnemlHabitatsPipelineOperationsServices:
    PUBLISH_OUTPUTS_AS_DATASET = _PrivateServices.PUBLISH_OUTPUTS_AS_DATASET
