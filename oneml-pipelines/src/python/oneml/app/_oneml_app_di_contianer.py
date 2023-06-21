import logging
from pathlib import Path
from typing import Any, Union

from oneml.io import (
    FilesystemUriFormatter,
    IFormatUri,
    InMemoryRW,
    InMemoryUriFormatter,
    IReadAndWriteData,
    OnemlIoServices,
    PickleLocalRW,
)
from oneml.pipelines.building import PipelineBuilderClient, PipelineBuilderFactory
from oneml.pipelines.data._filesystem import BlobFilesystem, LocalFilesystem
from oneml.pipelines.registry._pipeline_registry import PipelineRegistry
from oneml.pipelines.session import OnemlSessionServices, SessionDataClient
from oneml.pipelines.session._running_session_registry import RunningSessionRegistry
from oneml.pipelines.session._session_components import PipelineSessionComponents
from oneml.services import IProvideServices, group, provider
from oneml.services._context import ContextClient

from ._app_plugins import OnemlAppEntryPointPluginRelay
from ._oneml_app_services import OnemlAppServiceGroups, OnemlAppServices

logger = logging.getLogger(__name__)


class OnemlAppDiContainer:
    _app: IProvideServices

    def __init__(self, app: IProvideServices) -> None:
        self._app = app

    @provider(OnemlAppServices.PIPELINE_BUILDER_FACTORY)
    def pipeline_builder_factory(self) -> PipelineBuilderFactory:
        return PipelineBuilderFactory(
            session_components=self.pipeline_session_components(),
        )

    @provider(OnemlAppServices.PIPELINE_BUILDER)
    def pipeline_builder(self) -> PipelineBuilderClient:
        return PipelineBuilderClient(
            session_components=self.pipeline_session_components(),
        )

    @provider(OnemlSessionServices.PIPELINE_SESSION_COMPONENTS)
    def pipeline_session_components(self) -> PipelineSessionComponents:
        # TODO: I think we can delete this library and use the service containers
        return PipelineSessionComponents(
            running_session_registry=self._app.get_service(
                OnemlSessionServices.RUNNING_SESSION_REGISTRY
            ),
            services=self._app.get_service(OnemlAppServices.SERVICES_REGISTRY),
            context_client=self._app.get_service(OnemlAppServices.APP_CONTEXT_CLIENT),
            session_data_client=self._app.get_service(OnemlSessionServices.SESSION_DATA_CLIENT),
        )

    @provider(OnemlSessionServices.RUNNING_SESSION_REGISTRY)
    def running_session_registry(self) -> RunningSessionRegistry:
        return RunningSessionRegistry()

    @provider(OnemlSessionServices.SESSION_DATA_CLIENT)
    def session_data_client(self) -> SessionDataClient:
        return SessionDataClient(self._app)

    @provider(OnemlIoServices.INMEMORY_URI_FORMATTER)
    def inmemory_uri_formatter(self) -> IFormatUri[Any]:
        return InMemoryUriFormatter()

    @provider(OnemlIoServices.FILESYSTEM_URI_FORMATTER)
    def filesystem_uri_formatter(self) -> IFormatUri[Any]:
        return FilesystemUriFormatter(path=Path("../.tmp/"))

    @provider(OnemlIoServices.INMEMORY_RW)
    def inmemory_rw(self) -> IReadAndWriteData[Any]:
        return InMemoryRW()

    @provider(OnemlIoServices.PICKLE_LOCAL_RW)
    def pickle_local_rw(self) -> IReadAndWriteData[object]:
        return PickleLocalRW()

    # @provider(OnemlAppServices.REMOTE_EXECUTABLE_FACTORY)
    # def remote_executable_factory(self) -> RemoteExecutableFactory:
    #     raise NotImplementedError()
    #     # TODO: clean up this wiring and see if we can eliminate some of these classes now
    #     # return RemoteExecutableFactory(
    #     #     context=RemoteContext(self._app.get_service(OnemlAppServices.PIPELINE_SETTINGS)),
    #     #     driver=K8sExecutableProxy(
    #     #         # session_provider=self._app.get_service(OnemlAppServices.PIPELINE_SESSION_CONTEXT),
    #     #         settings_provider=self._app.get_service(OnemlAppServices.PIPELINE_SETTINGS),
    #     #         cmd_client=self._cmd_client(),
    #     #     ),
    #     #     pickler=ExecutablePicklingClient(
    #     #         fs_client=self._pickled_executables_fs_client(),
    #     #     ),
    #     # )

    # @provider(OnemlAppServices.PIPELINE_SETTINGS)
    # def pipeline_settings(self) -> PipelineSettingsClient:
    #     return PipelineSettingsClient()

    @provider(OnemlAppServices.SERVICES_REGISTRY)
    def services_registry(self) -> IProvideServices:
        return self._app

    @provider(OnemlAppServices.PIPELINE_REGISTRY)
    def session_registry(self) -> PipelineRegistry:
        return PipelineRegistry()

    @group(OnemlAppServiceGroups.APP_PLUGINS)
    def entry_point_plugin(self) -> OnemlAppEntryPointPluginRelay:
        return OnemlAppEntryPointPluginRelay(group="oneml.app_plugins")

    def _pickled_executables_fs_client(self) -> Union[LocalFilesystem, BlobFilesystem]:
        # TODO: find a more reliable way to get a tmp path
        return LocalFilesystem(directory=Path("../.tmp/"))
        # return BlobFilesystem(
        #     # TODO: switch to immunodata blob clients here
        #     credentials=ChainedTokenCredential(
        #         AzureCliCredential(),  # type: ignore
        #         ManagedIdentityCredential(),  # type: ignore
        #     ),
        #     # TODO: move these to a habitat config
        #     account="onemltmp2",
        #     container="onemltmp2",
        # )

    @provider(OnemlAppServices.APP_CONTEXT_CLIENT)
    def app_context_client(self) -> ContextClient:
        return ContextClient()
