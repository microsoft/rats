from functools import lru_cache
from pathlib import Path
from typing import Any, Union

from azure.identity import ManagedIdentityCredential

from oneml.habitats.example_hello_world._builder import NodeBasedPublisher, SimplePublisher
from oneml.habitats.immunocli._commands import OnemlPipelineNodeCommandFactory
from oneml.pipelines.building import PipelineBuilderFactory
from oneml.pipelines.building._executable_pickling import ExecutablePicklingClient
from oneml.pipelines.building._remote_execution import RemoteContext, RemoteExecutableFactory
from oneml.pipelines.context._client import ContextClient, IManageExecutionContexts
from oneml.pipelines.data._data_type_mapping import MappedPipelineDataClient
from oneml.pipelines.data._filesystem import BlobFilesystem, LocalFilesystem
from oneml.pipelines.data._memory_data_client import InMemoryDataClient
from oneml.pipelines.data._serialization import SerializationClient
from oneml.pipelines.k8s._executables import K8sExecutableProxy
from oneml.pipelines.session import IManagePipelineData, PipelineSessionClient
from oneml.pipelines.session._client import PipelineSessionComponents
from oneml.pipelines.settings import PipelineSettingsClient


class OnemlHabitatsPipelinesDiContainer:
    @lru_cache()
    def pipeline_builder_factory(self) -> PipelineBuilderFactory:
        return PipelineBuilderFactory(
            session_components=self.pipeline_session_components(),
            pipeline_settings=self.pipeline_settings(),
            remote_executable_factory=self._remote_executable_factory(),
        )

    @lru_cache()
    def simple_publisher(self) -> SimplePublisher[Any]:
        node_publisher = NodeBasedPublisher(
            session_context=self.pipeline_session_context()
        )
        return SimplePublisher(
            publisher=node_publisher,
        )

    @lru_cache()
    def _remote_executable_factory(self) -> RemoteExecutableFactory:
        return RemoteExecutableFactory(
            context=RemoteContext(self.pipeline_settings()),
            session_context=self.pipeline_session_context(),
            driver=K8sExecutableProxy(
                session_provider=self.pipeline_session_context(),
                settings_provider=self.pipeline_settings(),
                cmd_client=self._cmd_client(),
            ),
            pickler=ExecutablePicklingClient(
                fs_client=self._pickled_executables_fs_client(),
                session_context=self.pipeline_session_context(),
            ),
        )

    @lru_cache()
    def pipeline_session_components(self) -> PipelineSessionComponents:
        return PipelineSessionComponents(
            session_context=self.pipeline_session_context(),
            pipeline_data_client=self._pipeline_data_client(),
        )

    @lru_cache()
    def _pipeline_data_client(self) -> IManagePipelineData:
        # TODO: make this return a concrete type that knows of both memory and blob
        #       then change the return type of the method.
        return InMemoryDataClient()
        # return BlobDataClient(
        #     fs_client=self._pipeline_data_fs_client(),
        #     serializer=self._pipeline_serialization_client(),
        #     type_mapping=self._pipeline_type_mapping(),
        #     session_context=self.pipeline_session_context(),
        # )

    @lru_cache()
    def _pickled_executables_fs_client(self) -> Union[LocalFilesystem, BlobFilesystem]:
        # TODO: get the path from the immunoproject config
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

    @lru_cache()
    def _pipeline_data_fs_client(self) -> Union[LocalFilesystem, BlobFilesystem]:
        return BlobFilesystem(
            # TODO: use immunodata identity here
            credentials=ManagedIdentityCredential(),
            # TODO: move these to a habitat config
            account="ampdatasetsdev01",
            container="general",
        )

    @lru_cache()
    def _pipeline_serialization_client(self) -> SerializationClient:
        client = SerializationClient()
        return client

    @lru_cache()
    def _pipeline_type_mapping(self) -> MappedPipelineDataClient:
        client = MappedPipelineDataClient()
        return client

    @lru_cache()
    def pipeline_session_context(self) -> IManageExecutionContexts[PipelineSessionClient]:
        return ContextClient()

    @lru_cache()
    def pipeline_settings(self) -> PipelineSettingsClient:
        return PipelineSettingsClient()

    @lru_cache()
    def _cmd_client(self) -> OnemlPipelineNodeCommandFactory:
        return OnemlPipelineNodeCommandFactory()
