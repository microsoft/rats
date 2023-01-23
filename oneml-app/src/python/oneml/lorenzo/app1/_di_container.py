from functools import lru_cache
from typing import Any, Tuple, Union

from azure.identity import AzureCliCredential, ChainedTokenCredential, ManagedIdentityCredential

from oneml.cli import CliRequest
from oneml.logging import LoggingClient
from oneml.lorenzo.sample_pipeline._provider import SimpleDependenciesProvider, SimpleProvider
from oneml.lorenzo.sample_pipeline._publisher import NodeBasedPublisher, SimplePublisher
from oneml.pipelines.building import PipelineBuilderFactory
from oneml.pipelines.building._executable_pickling import ExecutablePicklingClient
from oneml.pipelines.building._remote_execution import RemoteContext, RemoteExecutableFactory
from oneml.pipelines.context._client import ContextClient, IManageExecutionContexts
from oneml.pipelines.dag import PipelineNode
from oneml.pipelines.data._blob_data_client import BlobDataClient
from oneml.pipelines.data._data_type_mapping import MappedPipelineDataClient
from oneml.pipelines.data._filesystem import BlobFilesystem, LocalFilesystem
from oneml.pipelines.data._serialization import DemoSerializer, SerializationClient
from oneml.pipelines.k8s._executables import IProvideK8sNodeCmds, K8sExecutableProxy
from oneml.pipelines.session import IManagePipelineData, PipelineSessionClient
from oneml.pipelines.session._client import PipelineSessionComponents
from oneml.pipelines.session._components import ComponentId
from oneml.pipelines.settings import PipelineSettingsClient

from ._application import App1Application, CliRequestStack
from ._di_provider import DiProvider
from ._pipeline import App1Pipeline, App1PipelineExecutables


class CmdClient(IProvideK8sNodeCmds):
    def get_k8s_node_cmd(self, node: PipelineNode) -> Tuple[str, ...]:
        return "democli", "run-pipeline-node", node.key


class App1DiContainer(DiProvider):
    def __init__(self, cli_request: CliRequest) -> None:
        self._cli_request = cli_request

    @lru_cache()
    def application(self) -> App1Application:
        return App1Application(
            requests=self.cli_request_stack(),
            pipeline=self._pipeline(),
            pipeline_settings=self._pipeline_settings(),
        )

    def _pipeline(self) -> App1Pipeline:
        return App1Pipeline(
            pipeline_builder_factory=self._pipeline_builder_factory(),
            pipeline_executables=self.pipeline_executables(),
            type_mapping_client=self._pipeline_type_mapping(),
            serialization_client=self._pipeline_serialization_client(),
            demo_serializer=self._demo_serializer(),
        )

    @lru_cache()
    def pipeline_executables(self) -> App1PipelineExecutables:
        return App1PipelineExecutables(
            input_provider=self._simple_provider(),
            output_presenter=self._simple_presenter(),
        )

    @lru_cache()
    def _simple_provider(self) -> SimpleProvider[Any]:
        return SimpleProvider(provider=self._simple_dependencies_provider())

    @lru_cache()
    def _simple_presenter(self) -> SimplePublisher[Any]:
        return SimplePublisher(publisher=self._node_based_publisher())

    @lru_cache()
    def _simple_dependencies_provider(self) -> SimpleDependenciesProvider:
        return SimpleDependenciesProvider(session_context=self.pipeline_session_context())

    @lru_cache()
    def _node_based_publisher(self) -> NodeBasedPublisher:
        return NodeBasedPublisher(session_context=self.pipeline_session_context())

    @lru_cache()
    def _pipeline_builder_factory(self) -> PipelineBuilderFactory:
        return PipelineBuilderFactory(
            session_components=self.pipeline_session_components(),
            pipeline_settings=self._pipeline_settings(),
            remote_executable_factory=self._remote_executable_factory(),
        )

    @lru_cache()
    def _remote_executable_factory(self) -> RemoteExecutableFactory:
        return RemoteExecutableFactory(
            context=RemoteContext(self._pipeline_settings()),
            session_context=self.pipeline_session_context(),
            driver=K8sExecutableProxy(
                session_provider=self.pipeline_session_context(),
                settings_provider=self._pipeline_settings(),
                cmd_client=CmdClient(),
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
        # return InMemoryDataClient()
        return BlobDataClient(
            fs_client=self._pipeline_data_fs_client(),
            serializer=self._pipeline_serialization_client(),
            type_mapping=self._pipeline_type_mapping(),
            session_context=self.pipeline_session_context(),
        )

    @lru_cache()
    def _pickled_executables_fs_client(self) -> Union[LocalFilesystem, BlobFilesystem]:
        return BlobFilesystem(
            credentials=ChainedTokenCredential(
                AzureCliCredential(),
                ManagedIdentityCredential(),
            ),
            account="onemltmp2",
            container="onemltmp2",
        )
        # return LocalFilesystem(directory=Path("../.tmp/"))

    @lru_cache()
    def _pipeline_data_fs_client(self) -> Union[LocalFilesystem, BlobFilesystem]:
        return BlobFilesystem(
            credentials=ManagedIdentityCredential(),
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

    def _demo_serializer(self) -> DemoSerializer[Any]:
        return DemoSerializer()

    @lru_cache()
    def pipeline_session_context(self) -> IManageExecutionContexts[PipelineSessionClient]:
        return ContextClient()

    @lru_cache()
    def _pipeline_settings(self) -> PipelineSettingsClient:
        return PipelineSettingsClient()

    @lru_cache()
    def cli_request_stack(self) -> CliRequestStack:
        return CliRequestStack()

    @lru_cache()
    def logging_client(self) -> LoggingClient:
        return LoggingClient()


App1DiComponent = ComponentId[App1DiContainer](__name__)
