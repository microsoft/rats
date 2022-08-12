from ._executable import CallableExecutable
from ._node_dependencies import IManagePipelineNodeDependencies
from ._node_execution import PipelineNodeExecutablesClient
from ._node_state import IManagePipelineNodeState, PipelineNodeState, PipelineNodeStateClient
from ._nodes import IManagePipelineNodes
from ._session import IPipelineSession, ITickablePipeline, PipelineSession
from ._session_frame import BasicPipelineSessionFrameCommands, PipelineSessionFrame
from ._session_state import IManagePipelineSessionState, PipelineSessionStateClient


class PipelineSessionComponents:

    _session_client: IPipelineSession
    _session_frame: ITickablePipeline
    # TODO: rename to session_state_client
    _session_state_client: IManagePipelineSessionState
    _node_state_client: IManagePipelineNodeState

    def __init__(
            self,
            session_client: IPipelineSession,
            session_frame: ITickablePipeline,
            session_state_client: IManagePipelineSessionState,
            node_state_client: IManagePipelineNodeState):
        self._session_client = session_client
        self._session_frame = session_frame
        self._session_state_client = session_state_client
        self._node_state_client = node_state_client

    def pipeline_session_client(self) -> IPipelineSession:
        return self._session_client

    def pipeline_frame_client(self) -> ITickablePipeline:
        return self._session_frame

    def pipeline_state_client(self) -> IManagePipelineSessionState:
        return self._session_state_client

    def node_state_client(self) -> IManagePipelineNodeState:
        return self._node_state_client


class PipelineSessionComponentsFactory:

    def get_instance(
            self,
            node_client: IManagePipelineNodes,
            node_dependencies_client: IManagePipelineNodeDependencies,
            node_executables_client: PipelineNodeExecutablesClient) -> PipelineSessionComponents:
        session_state_client = PipelineSessionStateClient()
        node_state_client = PipelineNodeStateClient()

        for node in node_client.get_nodes():
            node_state_client.set_node_state(node, PipelineNodeState.REGISTERED)

        frame_commands = BasicPipelineSessionFrameCommands(
            session_state_client=session_state_client,
            node_state_client=node_state_client,
            node_dependencies_client=node_dependencies_client,
            node_executable_client=node_executables_client,
        )

        frame = PipelineSessionFrame(tuple([
            CallableExecutable(frame_commands.promote_registered_nodes),
            CallableExecutable(frame_commands.promote_queued_nodes),
            CallableExecutable(frame_commands.execute_pending_nodes),
            CallableExecutable(frame_commands.check_pipeline_completion),
        ]))

        session = PipelineSession(
            session_state_client=session_state_client,
            pipeline=frame,
        )

        return PipelineSessionComponents(
            session_client=session,
            session_frame=frame,
            session_state_client=session_state_client,
            node_state_client=node_state_client,
        )
