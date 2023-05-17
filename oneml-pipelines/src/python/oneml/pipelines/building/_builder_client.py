from abc import abstractmethod
from functools import lru_cache
from typing import Any, Iterable, Protocol

from oneml.pipelines.context._client import IProvideExecutionContexts
from oneml.pipelines.dag import PipelineClient, PipelineDataDependency, PipelineNode, PipelinePort
from oneml.pipelines.data._serialization import DataType, DataTypeId
from oneml.pipelines.session import (
    IExecutable,
    IOManagerClient,
    IOManagerId,
    PipelineSessionClient,
    PipelineSessionClientFactory,
    PipelineSessionPluginClient,
)
from oneml.pipelines.session._client import PipelineSessionComponents
from oneml.pipelines.settings import IProvidePipelineSettings

from ._dag_client import IPipelineDagClient, PipelineDagClient
from ._executable_pickling import PickleableExecutable
from ._executables_client import IManageBuilderExecutables, PipelineBuilderExecutablesClient
from ._node_multiplexing import (
    IMultiplexPipelineNodes,
    PipelineMultiplexValuesType,
    PipelineNodeMultiplexer,
    PipelineNodeMultiplexerFactory,
)
from ._node_namespacing import (
    ICreatePipelineNamespaces,
    INamespacePipelineNodes,
    PipelineNamespaceClient,
)
from ._remote_execution import IProvideRemoteExecutables


class PipelineBuilderClient(
    IPipelineDagClient,
    IManageBuilderExecutables,
    ICreatePipelineNamespaces,
    INamespacePipelineNodes,
    IMultiplexPipelineNodes,
):
    _session_components: PipelineSessionComponents
    _pipeline_settings: IProvidePipelineSettings
    _remote_executable_factory: IProvideRemoteExecutables

    def __init__(
        self,
        session_components: PipelineSessionComponents,
        pipeline_settings: IProvidePipelineSettings,
        remote_executable_factory: IProvideRemoteExecutables,
    ) -> None:
        self._session_components = session_components
        self._pipeline_settings = pipeline_settings
        self._remote_executable_factory = remote_executable_factory

    def add_nodes(self, nodes: Iterable[PipelineNode]) -> None:
        self.get_dag_client().add_nodes(nodes)

    def add_node(self, node: PipelineNode) -> None:
        self.get_dag_client().add_node(node)

    def add_data_dependencies(
        self, node: PipelineNode, dependencies: Iterable[PipelineDataDependency[Any]]
    ) -> None:
        self.get_dag_client().add_data_dependencies(node, dependencies)

    def add_data_dependency(
        self, node: PipelineNode, dependency: PipelineDataDependency[Any]
    ) -> None:
        self.get_dag_client().add_data_dependency(node, dependency)

    def add_dependencies(self, node: PipelineNode, dependencies: Iterable[PipelineNode]) -> None:
        self.get_dag_client().add_dependencies(node, dependencies)

    def add_dependency(self, node: PipelineNode, dependency: PipelineNode) -> None:
        self.get_dag_client().add_dependency(node, dependency)

    def add_iomanager(
        self,
        node: PipelineNode,
        port: PipelinePort[DataType],
        iomanager_id: IOManagerId,
        type_id: DataTypeId[DataType],
    ) -> None:
        self._iomanager_client().register(node, port, iomanager_id, type_id)

    def build_session(self) -> PipelineSessionClient:
        return self.get_session_client_factory().get_instance(self.build())

    def build(self) -> PipelineClient:
        return self.get_dag_client().build()

    def add_remote_executable(self, node: PipelineNode, executable: PickleableExecutable) -> None:
        self.add_executable(node, self._remote_executable(executable))

    def add_executable(self, node: PipelineNode, executable: IExecutable) -> None:
        self.get_executables_client().add_executable(node, executable)

    def _remote_executable(self, executable: PickleableExecutable) -> IExecutable:
        # TODO: this is not an ideal API because this method is exposing the concept of
        #       driver/executor. This might be better served in the k8s specific session logic.
        return self._remote_executable_factory.get_instance(executable)

    def namespace(self, name: str) -> PipelineNamespaceClient:
        return self.get_namespace_client().namespace(name)

    def nodes(self, names: Iterable[str]) -> Iterable[PipelineNode]:
        return self.get_namespace_client().nodes(names)

    def node(self, name: str) -> PipelineNode:
        return self.get_namespace_client().node(name)

    def head_node(self) -> PipelineNode:
        return self.get_namespace_client().head_node()

    def tail_node(self) -> PipelineNode:
        return self.get_namespace_client().tail_node()

    def multiplex(self, values: PipelineMultiplexValuesType) -> PipelineNodeMultiplexer:
        return self.get_multiplex_client().get_instance(self.get_namespace_client(), values)

    @lru_cache()
    def get_namespace_client(self) -> PipelineNamespaceClient:
        return PipelineNamespaceClient("/")

    @lru_cache()
    def get_multiplex_client(self) -> PipelineNodeMultiplexerFactory:
        return PipelineNodeMultiplexerFactory(pipeline=self.get_dag_client())

    @lru_cache()
    def get_dag_client(self) -> PipelineDagClient:
        return PipelineDagClient()

    @lru_cache()
    def get_executables_client(self) -> PipelineBuilderExecutablesClient:
        return PipelineBuilderExecutablesClient(
            session_plugin_client=self.get_session_plugin_client(),
        )

    def get_session_client_factory(self) -> PipelineSessionClientFactory:
        return self._session_components.session_client_factory()

    def get_session_plugin_client(self) -> PipelineSessionPluginClient:
        return self._session_components.session_plugin_client()

    def _session_context(self) -> IProvideExecutionContexts[PipelineSessionClient]:
        return self._session_components.session_context()

    def _iomanager_client(self) -> IOManagerClient:
        return self._session_components.iomanager_client()


class DefaultDataTypeMapper:
    _mapper: dict[type[Any], DataTypeId[Any]]

    def __init__(self) -> None:
        self._mapper = {}

    def register(self, type_: type[Any], type_id: DataTypeId[Any], override: bool = False) -> None:
        if type_ in self._mapper and not override:
            raise ValueError(f"Type {type_} already registered.")
        self._mapper[type_] = type_id

    def __getitem__(self, type_: type[Any]) -> DataTypeId[Any]:
        return self._mapper[type_]


class IPipelineBuilderFactory(Protocol):
    @abstractmethod
    def get_instance(self) -> PipelineBuilderClient:
        ...

    @abstractmethod
    def get_default_datatype_mapper(self) -> DefaultDataTypeMapper:
        ...


class PipelineBuilderFactory(IPipelineBuilderFactory):
    _session_components: PipelineSessionComponents
    _default_datatype_mapper: DefaultDataTypeMapper
    _pipeline_settings: IProvidePipelineSettings
    _remote_executable_factory: IProvideRemoteExecutables

    def __init__(
        self,
        session_components: PipelineSessionComponents,
        default_datatype_mapper: DefaultDataTypeMapper,
        pipeline_settings: IProvidePipelineSettings,
        remote_executable_factory: IProvideRemoteExecutables,
    ) -> None:
        self._session_components = session_components
        self._default_datatype_mapper = default_datatype_mapper
        self._pipeline_settings = pipeline_settings
        self._remote_executable_factory = remote_executable_factory

    def get_instance(self) -> PipelineBuilderClient:
        return PipelineBuilderClient(
            session_components=self._session_components,
            pipeline_settings=self._pipeline_settings,
            remote_executable_factory=self._remote_executable_factory,
        )

    def get_default_datatype_mapper(self) -> DefaultDataTypeMapper:
        return self._default_datatype_mapper
