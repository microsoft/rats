from typing import List

from oneml.pipelines.dag import PipelineNode, PipelineNodeClient, PipelineNodeDependenciesClient
from oneml.pipelines.session import (
    BasicPipelineSessionFrameCommands,
    CallableExecutable,
    IExecutable,
    IPipelineSessionFrame,
    PipelineNodeExecutablesClient,
    PipelineNodeState,
    PipelineNodeStateClient,
    PipelineSessionFrame,
    PipelineSessionState,
    PipelineSessionStateClient,
)


class TestBasicPipelineSessionFrameCommands:

    _node_client: PipelineNodeClient
    _session_state_client: PipelineSessionStateClient
    _node_state_client: PipelineNodeStateClient
    _node_dependencies_client: PipelineNodeDependenciesClient
    _node_executable_client: PipelineNodeExecutablesClient
    _frame_commands: BasicPipelineSessionFrameCommands
    _foo: PipelineNode
    _bar: PipelineNode
    _executed_nodes: List[PipelineNode]

    def setup(self) -> None:
        self._node_client = PipelineNodeClient()
        self._session_state_client = PipelineSessionStateClient()
        self._node_state_client = PipelineNodeStateClient()
        self._node_dependencies_client = PipelineNodeDependenciesClient(self._node_client)
        self._node_executable_client = PipelineNodeExecutablesClient()

        self._frame_commands = BasicPipelineSessionFrameCommands(
            session_state_client=self._session_state_client,
            node_state_client=self._node_state_client,
            node_dependencies_client=self._node_dependencies_client,
            node_executables_client=self._node_executable_client,
        )
        self._foo = PipelineNode("foo")
        self._bar = PipelineNode("bar")
        self._node_executable_client.register_node_executable(
            self._foo, self._node_executable(self._foo))
        self._node_executable_client.register_node_executable(
            self._bar, self._node_executable(self._bar))
        self._executed_nodes = []

    def test_promote_node_steps(self) -> None:
        self._node_client.register_node(self._foo)
        self._node_client.register_node(self._bar)

        self._node_state_client.set_node_state(self._foo, PipelineNodeState.REGISTERED)
        self._node_state_client.set_node_state(self._bar, PipelineNodeState.COMPLETED)

        self._frame_commands.promote_registered_nodes()
        assert self._node_state_client.get_node_state(self._foo) == PipelineNodeState.QUEUED
        assert self._node_state_client.get_node_state(self._bar) == PipelineNodeState.COMPLETED

        self._frame_commands.promote_queued_nodes()
        assert self._node_state_client.get_node_state(self._foo) == PipelineNodeState.PENDING
        assert self._node_state_client.get_node_state(self._bar) == PipelineNodeState.COMPLETED

    def test_execute_pending_nodes(self) -> None:
        self._node_client.register_node(self._foo)
        self._node_client.register_node(self._bar)

        self._node_state_client.set_node_state(self._foo, PipelineNodeState.PENDING)
        self._node_state_client.set_node_state(self._bar, PipelineNodeState.REGISTERED)

        assert len(self._executed_nodes) == 0
        self._frame_commands.execute_pending_nodes()
        assert self._foo in self._executed_nodes and len(self._executed_nodes) == 1

        self._node_state_client.set_node_state(self._bar, PipelineNodeState.PENDING)
        self._frame_commands.execute_pending_nodes()
        assert self._bar in self._executed_nodes

    def test_check_pipeline_completion(self) -> None:
        self._node_client.register_node(self._foo)
        self._node_client.register_node(self._bar)

        self._node_state_client.set_node_state(self._foo, PipelineNodeState.RUNNING)
        self._node_state_client.set_node_state(self._bar, PipelineNodeState.RUNNING)

        self._session_state_client.set_state(PipelineSessionState.RUNNING)
        self._frame_commands.check_pipeline_completion()
        assert self._session_state_client.get_state() == PipelineSessionState.RUNNING

        self._node_state_client.set_node_state(self._foo, PipelineNodeState.COMPLETED)
        self._node_state_client.set_node_state(self._bar, PipelineNodeState.COMPLETED)
        self._frame_commands.check_pipeline_completion()
        assert self._session_state_client.get_state() == PipelineSessionState.STOPPED

    def _node_executable(self, node: PipelineNode) -> IExecutable:
        return CallableExecutable(lambda: self._executed_nodes.append(node))
