import logging

from rats.app import AppPlugin, RatsAppServices
from rats.services import (
    IManageServices,
    IProvideServices,
    ServiceId,
    after,
    scoped_service_ids,
    service_group,
    service_provider,
)

from ._plugin_register_rw import (
    IRegisterReadServiceForType,
    IRegisterWriteServiceForType,
    PluginRegisterReadersAndWriters,
)
from ._register_rw import RatsProcessorsRegisterReadersAndWriters
from .read_from_uri import (
    IGetReadServicesForType,
    IReadFromUriPipelineBuilder,
    ReadFromUriPipelineBuilder,
)
from .type_rw_mappers import (
    IGetWriteServicesForType,
    TypeToReadServiceMapper,
    TypeToWriteServiceMapper,
)
from .write_to_uri import (
    IWriteToNodeBasedUriPipelineBuilder,
    IWriteToRelativePathPipelineBuilder,
    IWriteToUriPipelineBuilder,
    WriteToNodeBasedUriPipelineBuilder,
    WriteToRelativePathPipelineBuilder,
    WriteToUriPipelineBuilder,
)

logger = logging.getLogger(__name__)


@scoped_service_ids
class _PrivateServices:
    # Things are grouped by making the service id name match
    # We create multiple entries here if we want to change the type (but not the id)
    REGISTER_TYPE_READER = ServiceId[IRegisterReadServiceForType]("type-to-read-service-mapper")
    GET_TYPE_READER = ServiceId[IGetReadServicesForType]("type-to-read-service-mapper")

    REGISTER_TYPE_WRITER = ServiceId[IRegisterWriteServiceForType]("type-to-write-service-mapper")
    GET_TYPE_WRITER = ServiceId[IGetWriteServicesForType]("type-to-write-service-mapper")

    READ_FROM_URI_PIPELINE_BUILDER = ServiceId[IReadFromUriPipelineBuilder](
        "read-from-uri-pipeline-builder"
    )
    WRITE_TO_URI_PIPELINE_BUILDER = ServiceId[IWriteToUriPipelineBuilder](
        "write-to-uri-pipeline-builder"
    )
    WRITE_TO_RELATIVE_PATH_PIPELINE_BUILDER = ServiceId[IWriteToRelativePathPipelineBuilder](
        "write-to-relative-path-pipeline-builder"
    )
    WRITE_TO_NODE_BASED_URI_PIPELINE_BUILDER = ServiceId[IWriteToNodeBasedUriPipelineBuilder](
        "write-to-node-based-uri-pipeline-builder"
    )
    PLUGIN_REGISTER_READERS_AND_WRITERS = ServiceId[PluginRegisterReadersAndWriters](
        "plugin-register-readers-and-writers"
    )


class RatsProcessorsIoDiContainer:
    _app: IProvideServices

    def __init__(self, app: IProvideServices) -> None:
        self._app = app

    @service_provider(_PrivateServices.REGISTER_TYPE_READER)
    def type_to_read_service_mapper(self) -> TypeToReadServiceMapper:
        return TypeToReadServiceMapper()

    @service_provider(_PrivateServices.REGISTER_TYPE_WRITER)
    def type_to_write_service_mapper(self) -> TypeToWriteServiceMapper:
        return TypeToWriteServiceMapper()

    @service_provider(_PrivateServices.READ_FROM_URI_PIPELINE_BUILDER)
    def read_from_url_pipeline_builder(self) -> ReadFromUriPipelineBuilder:
        return ReadFromUriPipelineBuilder(
            service_provider_service_id=RatsAppServices.SERVICE_CONTAINER,
            get_read_services_for_type=self._app.get_service(
                RatsProcessorsIoServices.GET_TYPE_READER
            ),
        )

    @service_provider(_PrivateServices.WRITE_TO_URI_PIPELINE_BUILDER)
    def write_to_url_pipeline_builder(self) -> WriteToUriPipelineBuilder:
        return WriteToUriPipelineBuilder(
            service_provider_service_id=RatsAppServices.SERVICE_CONTAINER,
            get_write_services_for_type=self._app.get_service(
                RatsProcessorsIoServices.GET_TYPE_WRITER
            ),
        )

    @service_provider(_PrivateServices.WRITE_TO_RELATIVE_PATH_PIPELINE_BUILDER)
    def write_to_relative_path_pipeline_builder(self) -> WriteToRelativePathPipelineBuilder:
        return WriteToRelativePathPipelineBuilder(
            write_to_uri_pipeline_builder=self._app.get_service(
                RatsProcessorsIoServices.WRITE_TO_URI_PIPELINE_BUILDER
            ),
        )

    @service_provider(_PrivateServices.WRITE_TO_NODE_BASED_URI_PIPELINE_BUILDER)
    def write_to_node_based_uri_pipeline_builder(self) -> WriteToNodeBasedUriPipelineBuilder:
        return WriteToNodeBasedUriPipelineBuilder(
            write_to_uri_pipeline_builder=self._app.get_service(
                RatsProcessorsIoServices.WRITE_TO_URI_PIPELINE_BUILDER
            ),
            context_provider_service_id=RatsAppServices.APP_CONTEXT_CLIENT,
        )

    @service_group(after(RatsAppServices.PLUGIN_LOAD_EXE))
    def register_readers_and_writers(self) -> PluginRegisterReadersAndWriters:
        return self._app.get_service(RatsProcessorsIoServices.PLUGIN_REGISTER_READERS_AND_WRITERS)

    @service_provider(_PrivateServices.PLUGIN_REGISTER_READERS_AND_WRITERS)
    def plugin_register_readers_and_writers(self) -> RatsProcessorsRegisterReadersAndWriters:
        return RatsProcessorsRegisterReadersAndWriters(
            readers_registry=self._app.get_service(RatsProcessorsIoServices.REGISTER_TYPE_READER),
            writers_registry=self._app.get_service(RatsProcessorsIoServices.REGISTER_TYPE_WRITER),
        )


class RatsProcessorsIoPlugin(AppPlugin):
    def load_plugin(self, app: IManageServices) -> None:
        logger.debug("initializing rats-processors-io plugin")
        app.parse_service_container(RatsProcessorsIoDiContainer(app))


class RatsProcessorsIoServices:
    REGISTER_TYPE_READER = _PrivateServices.REGISTER_TYPE_READER
    GET_TYPE_READER = _PrivateServices.GET_TYPE_READER
    REGISTER_TYPE_WRITER = _PrivateServices.REGISTER_TYPE_WRITER
    GET_TYPE_WRITER = _PrivateServices.GET_TYPE_WRITER
    READ_FROM_URI_PIPELINE_BUILDER = _PrivateServices.READ_FROM_URI_PIPELINE_BUILDER
    WRITE_TO_URI_PIPELINE_BUILDER = _PrivateServices.WRITE_TO_URI_PIPELINE_BUILDER
    WRITE_TO_RELATIVE_PATH_PIPELINE_BUILDER = (
        _PrivateServices.WRITE_TO_RELATIVE_PATH_PIPELINE_BUILDER
    )
    WRITE_TO_NODE_BASED_URI_PIPELINE_BUILDER = (
        _PrivateServices.WRITE_TO_NODE_BASED_URI_PIPELINE_BUILDER
    )
    PLUGIN_REGISTER_READERS_AND_WRITERS = _PrivateServices.PLUGIN_REGISTER_READERS_AND_WRITERS
