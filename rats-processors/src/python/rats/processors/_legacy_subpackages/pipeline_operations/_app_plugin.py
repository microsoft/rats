import logging

from rats.app import AppPlugin
from rats.processors._legacy_subpackages.io import RatsProcessorsIoServices
from rats.processors._legacy_subpackages.registry import ITransformPipeline
from rats.processors._legacy_subpackages.ux import UPipeline
from rats.services import (
    IManageServices,
    IProvideServices,
    ServiceId,
    scoped_service_ids,
    service_provider,
)

from ._collection_to_dict import CollectionToDict, DictToCollection
from ._duplicate_pipeline import DuplicatePipeline
from ._expose_given_outputs import ExposeGivenOutputs
from ._expose_pipeline_as_output import ExposePipelineAsOutput
from ._load_inputs_save_outputs import LoadInputsSaveOutputs
from ._write_manifest import AddOutputManifest

logger = logging.getLogger(__name__)


@scoped_service_ids
class _PrivateServices:
    DUPLICATE_PIPELINE = ServiceId[DuplicatePipeline]("duplicate-pipeline")
    EXPOSE_GIVEN_OUTPUTS = ServiceId[ExposeGivenOutputs]("expose-given-outputs")
    LOAD_INPUTS_SAVE_OUTPUTS = ServiceId[ITransformPipeline[UPipeline, UPipeline]](
        "load-inputs-save-outputs"
    )
    EXPOSE_PIPELINE_AS_OUTPUT = ServiceId[ITransformPipeline[UPipeline, UPipeline]](
        "expose-pipeline-as-output"
    )
    WRITE_MANIFEST = ServiceId[ITransformPipeline[UPipeline, UPipeline]]("write-manifest")
    COLLECTION_TO_DICT = ServiceId[CollectionToDict]("collection-to-dict")
    DICT_TO_COLLECTION = ServiceId[DictToCollection]("dict-to-collection")


class RatsProcessorsPipelineOperationsDiContainer:
    _app: IProvideServices

    def __init__(self, app: IProvideServices) -> None:
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
                RatsProcessorsIoServices.READ_FROM_URI_PIPELINE_BUILDER
            ),
            write_to_node_based_uri=self._app.get_service(
                RatsProcessorsIoServices.WRITE_TO_NODE_BASED_URI_PIPELINE_BUILDER
            ),
        )

    @service_provider(_PrivateServices.WRITE_MANIFEST)
    def write_manifest(self) -> AddOutputManifest:
        return AddOutputManifest(
            write_to_relative_path=self._app.get_service(
                RatsProcessorsIoServices.WRITE_TO_RELATIVE_PATH_PIPELINE_BUILDER
            )
        )

    @service_provider(_PrivateServices.COLLECTION_TO_DICT)
    def collection_to_dict(self) -> CollectionToDict:
        return CollectionToDict()

    @service_provider(_PrivateServices.DICT_TO_COLLECTION)
    def dict_to_collection(self) -> DictToCollection:
        return DictToCollection()


class RatsProcessorsPipelineOperationsPlugin(AppPlugin):
    def load_plugin(self, app: IManageServices) -> None:
        logger.debug("initializing rats-processors-pipeline-operations plugin")
        app.parse_service_container(RatsProcessorsPipelineOperationsDiContainer(app))


class RatsProcessorsPipelineOperationsServices:
    DUPLICATE_PIPELINE = _PrivateServices.DUPLICATE_PIPELINE
    EXPOSE_GIVEN_OUTPUTS = _PrivateServices.EXPOSE_GIVEN_OUTPUTS
    LOAD_INPUTS_SAVE_OUTPUTS = _PrivateServices.LOAD_INPUTS_SAVE_OUTPUTS
    EXPOSE_PIPELINE_AS_OUTPUT = _PrivateServices.EXPOSE_PIPELINE_AS_OUTPUT
    WRITE_MANIFEST = _PrivateServices.WRITE_MANIFEST
    COLLECTION_TO_DICT = _PrivateServices.COLLECTION_TO_DICT
    DICT_TO_COLLECTION = _PrivateServices.DICT_TO_COLLECTION
