from functools import lru_cache
from pathlib import Path
from tempfile import mkdtemp

from oneml.io2 import (
    LocalIoSettings,
    LocalJsonIoPlugin,
    LocalJsonIoSettings,
    LocalJsonWriter,
    OnemlIoOnNodeCompletion,
    OnemlIoPlugin,
    PipelineData,
)
from oneml.pipelines.session import OnemlSessionContexts
from oneml.services import (
    IExecutable,
    IProvideServices,
    ServiceId,
    after,
    scoped_service_ids,
    service_group,
    service_provider,
)

from ._oneml_app_services import OnemlAppServices
from ._session_services import OnemlSessionExecutables


@scoped_service_ids
class OnemlIo2Services:
    PIPELINE_DATA = ServiceId[PipelineData]("pipeline-data")
    LOCAL_IO_SETTINGS = ServiceId[LocalIoSettings]("local-io-settings")
    LOCAL_JSON_WRITER = ServiceId[LocalJsonWriter]("local-json-writer")
    LOCAL_JSON_SETTINGS = ServiceId[LocalJsonIoSettings]("local-json-storage")


@scoped_service_ids
class OnemlIo2Groups:
    IO_PLUGIN = ServiceId[OnemlIoPlugin]("io-plugin")


class OnemlIo2DiContainer:
    _app: IProvideServices

    def __init__(self, app: IProvideServices) -> None:
        self._app = app

    @service_provider(OnemlIo2Services.PIPELINE_DATA)
    def pipeline_data(self) -> PipelineData:
        context_client = self._app.get_service(OnemlAppServices.APP_CONTEXT_CLIENT)
        return PipelineData(
            namespace=context_client.get_context_provider(OnemlSessionContexts.PIPELINE),
            node_ctx=context_client.get_context_provider(OnemlSessionContexts.NODE),
        )

    @service_provider(OnemlIo2Services.LOCAL_JSON_WRITER)
    def local_json_writer(self) -> LocalJsonWriter:
        context_client = self._app.get_service(OnemlAppServices.APP_CONTEXT_CLIENT)

        return LocalJsonWriter(
            io_settings=self._app.get_service(OnemlIo2Services.LOCAL_IO_SETTINGS),
            node_ctx=context_client.get_context_provider(OnemlSessionContexts.NODE),
            port_ctx=context_client.get_context_provider(OnemlSessionContexts.PORT),
        )

    @service_group(after(OnemlSessionExecutables.NODE))
    def on_node_completion(self) -> IExecutable:
        context_client = self._app.get_service(OnemlAppServices.APP_CONTEXT_CLIENT)
        return OnemlIoOnNodeCompletion(
            node_ctx=context_client.get_context_provider(OnemlSessionContexts.NODE),
            plugins=self._app.get_service_group(OnemlIo2Groups.IO_PLUGIN),
        )

    @service_group(OnemlIo2Groups.IO_PLUGIN)
    def local_json_plugin(self) -> LocalJsonIoPlugin:
        context_client = self._app.get_service(OnemlAppServices.APP_CONTEXT_CLIENT)
        return LocalJsonIoPlugin(
            source=self._app.get_service(OnemlIo2Services.PIPELINE_DATA),
            writer=self._app.get_service(OnemlIo2Services.LOCAL_JSON_WRITER),  # type: ignore
            node_ctx=context_client.get_context_provider(OnemlSessionContexts.NODE),
            storage=self._app.get_service(OnemlIo2Services.LOCAL_JSON_SETTINGS),
            port_opener=context_client.get_context_opener(OnemlSessionContexts.PORT),
        )

    @service_provider(OnemlIo2Services.LOCAL_IO_SETTINGS)
    def local_io_settings(self) -> LocalIoSettings:
        context_client = self._app.get_service(OnemlAppServices.APP_CONTEXT_CLIENT)

        @lru_cache()
        def default() -> Path:
            return Path(mkdtemp(prefix="oneml"))

        return LocalIoSettings(
            default_path=default,
            pipeline_ctx=context_client.get_context_provider(OnemlSessionContexts.PIPELINE),
        )

    @service_provider(OnemlIo2Services.LOCAL_JSON_SETTINGS)
    def local_json_storage(self) -> LocalJsonIoSettings:
        context_client = self._app.get_service(OnemlAppServices.APP_CONTEXT_CLIENT)
        return LocalJsonIoSettings(
            pipeline_ctx=context_client.get_context_provider(OnemlSessionContexts.PIPELINE),
        )
