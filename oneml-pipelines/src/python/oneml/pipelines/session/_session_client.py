from abc import abstractmethod
from typing import Protocol, TypeAlias

from oneml.pipelines.context._client import IManageExecutionContexts
from oneml.pipelines.dag import PipelineNode

from ._io_managers import IOManagerClient
from ._node_execution import IManagePipelineNodeExecutables
from ._node_state import IManagePipelineNodeState
from ._services import IProvideServices, ServiceId, ServiceType
from ._session_data_client import PipelineNodeDataClientFactory, PipelineNodeInputDataClientFactory
from ._session_frame import IPipelineSessionFrame
from ._session_state import IManagePipelineSessionState, PipelineSessionState


class IRunnablePipelineSession(Protocol):
    @abstractmethod
    def run(self) -> None:
        pass


class IStoppablePipelineSession(Protocol):
    @abstractmethod
    def stop(self) -> None:
        pass


class IPipelineSession(IRunnablePipelineSession, IStoppablePipelineSession, Protocol):
    pass


class PipelineSessionClient(IPipelineSession, IProvideServices):
    _session_id: str
    _services: IProvideServices
    _session_context: IManageExecutionContexts["PipelineSessionClient"]
    _session_frame: IPipelineSessionFrame
    _iomanager_client: IOManagerClient
    _session_executables_client: IManagePipelineNodeExecutables
    _session_state_client: IManagePipelineSessionState
    _node_state_client: IManagePipelineNodeState
    _node_data_client_factory: PipelineNodeDataClientFactory
    _node_executables_client: IManagePipelineNodeExecutables
    _node_input_data_client_factory: PipelineNodeInputDataClientFactory

    def __init__(
        self,
        session_id: str,
        services: IProvideServices,
        session_context: IManageExecutionContexts["PipelineSessionClient"],
        session_frame: IPipelineSessionFrame,
        session_state_client: IManagePipelineSessionState,
        iomanager_client: IOManagerClient,
        session_executables_client: IManagePipelineNodeExecutables,
        node_state_client: IManagePipelineNodeState,
        node_data_client_factory: PipelineNodeDataClientFactory,
        node_executables_client: IManagePipelineNodeExecutables,
        node_input_data_client_factory: PipelineNodeInputDataClientFactory,
    ):
        self._session_id = session_id
        self._services = services
        self._session_context = session_context
        self._session_frame = session_frame
        self._session_state_client = session_state_client
        self._iomanager_client = iomanager_client
        self._session_executables_client = session_executables_client
        self._node_state_client = node_state_client
        self._node_data_client_factory = node_data_client_factory
        self._node_executables_client = node_executables_client
        self._node_input_data_client_factory = node_input_data_client_factory

    def get_service(self, component_id: ServiceId[ServiceType]) -> ServiceType:
        return self._services.get_service(component_id)

    def run(self) -> None:
        with self._session_context.execution_context(self):
            self._session_state_client.set_state(PipelineSessionState.RUNNING)
            while self._session_state_client.get_state() == PipelineSessionState.RUNNING:
                self._session_frame.tick()

    def run_node(self, node: PipelineNode) -> None:
        with self._session_context.execution_context(self):
            self._session_state_client.set_state(PipelineSessionState.RUNNING)
            self.session_executables_client().execute_node(node)

    def stop(self) -> None:
        self._session_state_client.set_state(PipelineSessionState.STOPPED)

    def session_id(self) -> str:
        return self._session_id

    def pipeline_frame_client(self) -> IPipelineSessionFrame:
        return self._session_frame

    def pipeline_state_client(self) -> IManagePipelineSessionState:
        return self._session_state_client

    def iomanager_client(self) -> IOManagerClient:
        return self._iomanager_client

    def session_executables_client(self) -> IManagePipelineNodeExecutables:
        return self._session_executables_client

    def node_state_client(self) -> IManagePipelineNodeState:
        return self._node_state_client

    def node_data_client_factory(self) -> PipelineNodeDataClientFactory:
        return self._node_data_client_factory

    def node_executables_client(self) -> IManagePipelineNodeExecutables:
        return self._node_executables_client

    def node_input_data_client_factory(self) -> PipelineNodeInputDataClientFactory:
        return self._node_input_data_client_factory


PipelineSessionContext: TypeAlias = IManageExecutionContexts[PipelineSessionClient]
