from functools import lru_cache
from pathlib import Path
from tempfile import mkdtemp

from rats.io2 import (
    LocalIoSettings,
    LocalJsonIoPlugin,
    LocalJsonIoSettings,
    LocalJsonWriter,
    PipelineData,
    RatsIoOnNodeCompletion,
    RatsIoPlugin,
)
from rats.pipelines.session import RatsSessionContexts
from rats.services import (
    IExecutable,
    IProvideServices,
    ServiceId,
    after,
    scoped_service_ids,
    service_group,
    service_provider,
)

from ._rats_app_services import RatsAppServices
from ._session_services import RatsSessionExecutables


@scoped_service_ids
class RatsIo2Services:
    PIPELINE_DATA = ServiceId[PipelineData]("pipeline-data")
    LOCAL_IO_SETTINGS = ServiceId[LocalIoSettings]("local-io-settings")
    LOCAL_JSON_WRITER = ServiceId[LocalJsonWriter]("local-json-writer")
    LOCAL_JSON_SETTINGS = ServiceId[LocalJsonIoSettings]("local-json-storage")


@scoped_service_ids
class RatsIo2Groups:
    IO_PLUGIN = ServiceId[RatsIoPlugin]("io-plugin")


class RatsIo2DiContainer:
    _app: IProvideServices

    def __init__(self, app: IProvideServices) -> None:
        self._app = app

    @service_provider(RatsIo2Services.PIPELINE_DATA)
    def pipeline_data(self) -> PipelineData:
        context_client = self._app.get_service(RatsAppServices.APP_CONTEXT_CLIENT)
        return PipelineData(
            namespace=context_client.get_context_provider(RatsSessionContexts.PIPELINE),
            node_ctx=context_client.get_context_provider(RatsSessionContexts.NODE),
        )

    @service_provider(RatsIo2Services.LOCAL_JSON_WRITER)
    def local_json_writer(self) -> LocalJsonWriter:
        context_client = self._app.get_service(RatsAppServices.APP_CONTEXT_CLIENT)

        return LocalJsonWriter(
            io_settings=self._app.get_service(RatsIo2Services.LOCAL_IO_SETTINGS),
            node_ctx=context_client.get_context_provider(RatsSessionContexts.NODE),
            port_ctx=context_client.get_context_provider(RatsSessionContexts.PORT),
        )

    @service_group(after(RatsSessionExecutables.NODE))
    def on_node_completion(self) -> IExecutable:
        context_client = self._app.get_service(RatsAppServices.APP_CONTEXT_CLIENT)
        return RatsIoOnNodeCompletion(
            node_ctx=context_client.get_context_provider(RatsSessionContexts.NODE),
            plugins=self._app.get_service_group(RatsIo2Groups.IO_PLUGIN),
        )

    @service_group(RatsIo2Groups.IO_PLUGIN)
    def local_json_plugin(self) -> LocalJsonIoPlugin:
        context_client = self._app.get_service(RatsAppServices.APP_CONTEXT_CLIENT)
        writer = self._app.get_service(RatsIo2Services.LOCAL_JSON_WRITER)
        return LocalJsonIoPlugin(
            source=self._app.get_service(RatsIo2Services.PIPELINE_DATA),
            writer=writer,
            node_ctx=context_client.get_context_provider(RatsSessionContexts.NODE),
            storage=self._app.get_service(RatsIo2Services.LOCAL_JSON_SETTINGS),
            port_opener=context_client.get_context_opener(RatsSessionContexts.PORT),
        )

    @service_provider(RatsIo2Services.LOCAL_IO_SETTINGS)
    def local_io_settings(self) -> LocalIoSettings:
        context_client = self._app.get_service(RatsAppServices.APP_CONTEXT_CLIENT)

        @lru_cache
        def default() -> Path:
            return Path(mkdtemp(prefix="rats"))

        return LocalIoSettings(
            default_path=default,
            pipeline_ctx=context_client.get_context_provider(RatsSessionContexts.PIPELINE),
        )

    @service_provider(RatsIo2Services.LOCAL_JSON_SETTINGS)
    def local_json_storage(self) -> LocalJsonIoSettings:
        context_client = self._app.get_service(RatsAppServices.APP_CONTEXT_CLIENT)
        return LocalJsonIoSettings(
            pipeline_ctx=context_client.get_context_provider(RatsSessionContexts.PIPELINE),
        )
