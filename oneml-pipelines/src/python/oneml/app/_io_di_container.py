from pathlib import Path
from typing import Any

from oneml.io import (
    DefaultIoRw,
    DillLocalRW,
    FilesystemUriFormatter,
    IFormatUri,
    InMemoryRW,
    InMemoryUriFormatter,
    IReadAndWriteData,
    NodeOutputClient,
    OnemlIoServices,
    PipelineLoaderGetter,
    PipelinePublisherGetter,
)
from oneml.pipelines.session import OnemlSessionContexts
from oneml.services import IProvideServices, after, service_group, service_provider

from ._oneml_app_services import OnemlAppServices


class OnemlIoDiContainer:
    _app: IProvideServices

    def __init__(self, app: IProvideServices) -> None:
        self._app = app

    @service_provider(OnemlIoServices.NODE_OUTPUT_CLIENT)
    def output_client(self) -> NodeOutputClient:
        context_client = self._app.get_service(OnemlAppServices.APP_CONTEXT_CLIENT)
        return NodeOutputClient(
            pipeline_context=context_client.get_context_provider(OnemlSessionContexts.PIPELINE),
            node_context=context_client.get_context_provider(OnemlSessionContexts.NODE),
            publishers=self._app.get_service(OnemlIoServices.PIPELINE_PUBLISHERS_GETTER),
        )

    @service_provider(OnemlIoServices.PIPELINE_PUBLISHERS_GETTER)
    def pipeline_publishers_getter(self) -> PipelinePublisherGetter[Any]:
        return PipelinePublisherGetter[Any](self._app)

    @service_provider(OnemlIoServices.PIPELINE_LOADERS_GETTER)
    def pipeline_loaders_getter(self) -> PipelineLoaderGetter[Any]:
        return PipelineLoaderGetter[Any](self._app)

    @service_provider(OnemlIoServices.INMEMORY_URI_FORMATTER)
    def inmemory_uri_formatter(self) -> IFormatUri[Any]:
        return InMemoryUriFormatter()

    @service_provider(OnemlIoServices.FILESYSTEM_URI_FORMATTER)
    def filesystem_uri_formatter(self) -> IFormatUri[Any]:
        return FilesystemUriFormatter(path=Path("../.tmp/"))

    @service_provider(OnemlIoServices.INMEMORY_RW)
    def inmemory_rw(self) -> IReadAndWriteData[Any]:
        return InMemoryRW()

    @service_provider(OnemlIoServices.DILL_LOCAL_RW)
    def dill_local_rw(self) -> IReadAndWriteData[object]:
        return DillLocalRW()

    @service_group(after(OnemlAppServices.PIPELINE_EXECUTABLE))
    def default_io_rw(self) -> DefaultIoRw:
        """Default IO handlers for the pipeline.

        After the user has defined a DAG, we use this service to traverse the data nodes and
        configure some default IO handlers.
        """
        context_client = self._app.get_service(OnemlAppServices.APP_CONTEXT_CLIENT)
        return DefaultIoRw(
            context=context_client.get_context_provider(OnemlSessionContexts.PIPELINE),
            dag_client=self._app.get_service(OnemlAppServices.PIPELINE_DAG_CLIENT),
            loaders=self._app.get_service(OnemlIoServices.PIPELINE_LOADERS_GETTER),
            publishers=self._app.get_service(OnemlIoServices.PIPELINE_PUBLISHERS_GETTER),
        )
