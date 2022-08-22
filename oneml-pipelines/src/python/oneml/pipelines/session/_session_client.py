from ._node_execution import IExecutePipelineNodes, IManagePipelineNodeExecutables
from ._node_state import IManagePipelineNodeState
from ._session import IPipelineSession
from ._session_data_client import IManagePipelineData, PipelineNodeDataClientFactory
from ._session_frame import IPipelineSessionFrame
from ._session_state import IManagePipelineSessionState


class PipelineSessionClient:

    _session_id: str
    _session_client: IPipelineSession
    _session_frame: IPipelineSessionFrame
    _pipeline_data_client: IManagePipelineData
    _session_executables_client: IExecutePipelineNodes
    _session_state_client: IManagePipelineSessionState
    _node_state_client: IManagePipelineNodeState
    _node_data_client_factory: PipelineNodeDataClientFactory
    _node_executables_client: IManagePipelineNodeExecutables

    def __init__(
            self,
            session_id: str,
            session_client: IPipelineSession,
            session_frame: IPipelineSessionFrame,
            session_state_client: IManagePipelineSessionState,
            pipeline_data_client: IManagePipelineData,
            session_executables_client: IExecutePipelineNodes,
            node_state_client: IManagePipelineNodeState,
            node_data_client_factory: PipelineNodeDataClientFactory,
            node_executables_client: IManagePipelineNodeExecutables):
        self._session_id = session_id
        self._session_client = session_client
        self._session_frame = session_frame
        self._session_state_client = session_state_client
        self._pipeline_data_client = pipeline_data_client
        self._session_executables_client = session_executables_client
        self._node_state_client = node_state_client
        self._node_data_client_factory = node_data_client_factory
        self._node_executables_client = node_executables_client

    def run(self) -> None:
        self._session_client.run()

    def pipeline_session(self) -> IPipelineSession:
        return self._session_client

    def pipeline_frame_client(self) -> IPipelineSessionFrame:
        return self._session_frame

    def pipeline_state_client(self) -> IManagePipelineSessionState:
        return self._session_state_client

    def pipeline_data_client(self) -> IManagePipelineData:
        return self._pipeline_data_client

    def session_executables_client(self) -> IExecutePipelineNodes:
        return self._session_executables_client

    def node_state_client(self) -> IManagePipelineNodeState:
        return self._node_state_client

    def node_data_client_factory(self) -> PipelineNodeDataClientFactory:
        return self._node_data_client_factory

    def node_executables_client(self) -> IManagePipelineNodeExecutables:
        return self._node_executables_client
