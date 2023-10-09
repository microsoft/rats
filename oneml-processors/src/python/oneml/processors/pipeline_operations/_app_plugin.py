import logging

from oneml.app import AppPlugin, OnemlApp
from oneml.services import (
    IManageServices,
    IProvideServices,
    ServiceId,
    scoped_service_ids,
    service_provider,
)

from ..services import OnemlProcessorsServices
from ._collection_to_dict import CollectionToDict, DictToCollection
from ._duplicate_pipeline import DuplicatePipeline
from ._expose_given_outputs import ExposeGivenOutputs
from ._expose_pipeline_as_output import ExposePipelineAsOutput
from ._load_inputs_save_outputs import LoadInputsSaveOutputs
from ._pipeline_provider import ITransformPipeline
from ._write_manifest import AddOutputManifest

logger = logging.getLogger(__name__)


@scoped_service_ids
class _PrivateServices:
    DUPLICATE_PIPELINE = ServiceId[DuplicatePipeline]("duplicate-pipeline")
    EXPOSE_GIVEN_OUTPUTS = ServiceId[ExposeGivenOutputs]("expose-given-outputs")
    LOAD_INPUTS_SAVE_OUTPUTS = ServiceId[ITransformPipeline]("load-inputs-save-outputs")
    EXPOSE_PIPELINE_AS_OUTPUT = ServiceId[ITransformPipeline]("expose-pipeline-as-output")
    WRITE_MANIFEST = ServiceId[ITransformPipeline]("write-manifest")
    COLLECTION_TO_DICT = ServiceId[CollectionToDict]("collection-to-dict")
    DICT_TO_COLLECTION = ServiceId[DictToCollection]("dict-to-collection")


class OnemlProcessorsPipelineOperationsDiContainer:
    _app: OnemlApp

    def __init__(self, app: IProvideServices) -> None:
        assert isinstance(app, OnemlApp)
        self._app = app

    @service_provider(_PrivateServices.DUPLICATE_PIPELINE)
    def duplicate_pipeline(self) -> DuplicatePipeline:
        return DuplicatePipeline()

    @service_provider(_PrivateServices.EXPOSE_PIPELINE_AS_OUTPUT)
    def expose_pipeline_as_output(self) -> ExposePipelineAsOutput:
        return ExposePipelineAsOutput(
            expose_given_outputs=self._app.get_service(_PrivateServices.EXPOSE_GIVEN_OUTPUTS)
        )

    @service_provider(_PrivateServices.EXPOSE_GIVEN_OUTPUTS)
    def expose_given_outputs(self) -> ExposeGivenOutputs:
        return ExposeGivenOutputs()

    @service_provider(_PrivateServices.LOAD_INPUTS_SAVE_OUTPUTS)
    def load_inputs_save_outputs(self) -> LoadInputsSaveOutputs:
        return LoadInputsSaveOutputs(
            read_from_uri=self._app.get_service(
                OnemlProcessorsServices.READ_FROM_URI_PIPELINE_BUILDER
            ),
            write_to_node_based_uri=self._app.get_service(
                OnemlProcessorsServices.WRITE_TO_NODE_BASED_URI_PIPELINE_BUILDER
            ),
        )

    @service_provider(_PrivateServices.WRITE_MANIFEST)
    def write_manifest(self) -> AddOutputManifest:
        return AddOutputManifest(
            write_to_relative_path=self._app.get_service(
                OnemlProcessorsServices.WRITE_TO_RELATIVE_PATH_PIPELINE_BUILDER
            )
        )

    @service_provider(_PrivateServices.COLLECTION_TO_DICT)
    def collection_to_dict(self) -> CollectionToDict:
        return CollectionToDict()

    @service_provider(_PrivateServices.DICT_TO_COLLECTION)
    def dict_to_collection(self) -> DictToCollection:
        return DictToCollection()


class OnemlProcessorsPipelineOperationsPlugin(AppPlugin):
    def load_plugin(self, app: IManageServices) -> None:
        logger.debug("initializing oneml-processors-pipeline-operations plugin")
        app.parse_service_container(OnemlProcessorsPipelineOperationsDiContainer(app))


class OnemlProcessorsPipelineOperationsServices:
    DUPLICATE_PIPELINE = _PrivateServices.DUPLICATE_PIPELINE
    EXPOSE_GIVEN_OUTPUTS = _PrivateServices.EXPOSE_GIVEN_OUTPUTS
    LOAD_INPUTS_SAVE_OUTPUTS = _PrivateServices.LOAD_INPUTS_SAVE_OUTPUTS
    EXPOSE_PIPELINE_AS_OUTPUT = _PrivateServices.EXPOSE_PIPELINE_AS_OUTPUT
    COLLECTION_TO_DICT = _PrivateServices.COLLECTION_TO_DICT
    DICT_TO_COLLECTION = _PrivateServices.DICT_TO_COLLECTION
