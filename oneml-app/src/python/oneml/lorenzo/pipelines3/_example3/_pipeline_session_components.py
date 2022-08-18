# type: ignore
# flake8: noqa
from abc import abstractmethod
from typing import Protocol

from oneml.lorenzo.pipelines3._example3._node_executable import PipelineNodeExecutablesClient
from oneml.lorenzo.pipelines3._example3._pipeline_session import (
    DemoPipelineSessionFrame,
    IPipelineSession,
    PipelineSession,
)
from oneml.pipelines import (
    ClosePipelineFrameCommand,
    ExecutePipelineFrameCommand,
    IManagePipelineNodeDependencies,
    IManagePipelineNodes,
    PipelineNodeState,
    PipelineNodeStateClient,
    PipelineSessionStateClient,
    PromoteQueuedNodesCommand,
    PromoteRegisteredNodesCommand,
)


class ITickablePipeline(Protocol):
    @abstractmethod
    def tick(self) -> None:
        pass


class PipelineSessionComponents:

    _pipeline_session: IPipelineSession
    _frame: ITickablePipeline
    _pipeline_state_client: PipelineSessionStateClient
    _node_state_client: PipelineNodeStateClient

    def __init__(
        self,
        pipeline_session: IPipelineSession,
        frame: ITickablePipeline,
        pipeline_state_client: PipelineSessionStateClient,
        node_state_client: PipelineNodeStateClient,
    ):
        self._pipeline_session = pipeline_session
        self._frame = frame
        self._pipeline_state_client = pipeline_state_client
        self._node_state_client = node_state_client

    def pipeline_session_client(self) -> IPipelineSession:
        return self._pipeline_session

    def pipeline_frame_client(self) -> ITickablePipeline:
        return self._frame

    def pipeline_state_client(self) -> PipelineSessionStateClient:
        return self._pipeline_state_client

    def node_state_client(self) -> PipelineNodeStateClient:
        return self._node_state_client


class PipelineSessionComponentsFactory:
    def get_instance(
        self,
        nodes_client: IManagePipelineNodes,
        dependencies_client: IManagePipelineNodeDependencies,
        executables_client: PipelineNodeExecutablesClient,
    ) -> PipelineSessionComponents:
        pipeline_state = PipelineSessionStateClient()
        node_state = PipelineNodeStateClient()

        for node in nodes_client.get_nodes():
            node_state.set_node_state(node, PipelineNodeState.REGISTERED)

        # frame commands
        registered = PromoteRegisteredNodesCommand(state_client=node_state)
        queued = PromoteQueuedNodesCommand(
            state_client=node_state,
            dependencies_client=dependencies_client,
        )
        execute = ExecutePipelineFrameCommand(
            state_client=node_state,
            runner=executables_client,
        )
        close = ClosePipelineFrameCommand(
            node_state_client=node_state,
            pipeline_state_client=pipeline_state,
        )

        frame = DemoPipelineSessionFrame(
            registered=registered,
            queued=queued,
            execute=execute,
            close=close,
        )

        session = PipelineSession(state_client=pipeline_state, pipeline=frame)

        return PipelineSessionComponents(
            pipeline_session=session,
            frame=frame,
            pipeline_state_client=pipeline_state,
            node_state_client=node_state,
        )
