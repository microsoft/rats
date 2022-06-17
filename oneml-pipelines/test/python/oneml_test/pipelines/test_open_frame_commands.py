from typing import Tuple

from oneml.pipelines import (
    IExecutable,
    IManagePipelineNodeDependencies,
    OpenPipelineFrameCommand,
    PipelineNode,
    PipelineNodeState,
    PipelineNodeStateClient,
    PromoteQueuedNodesCommand,
    PromoteRegisteredNodesCommand,
)


class FakeDependenciesClient(IManagePipelineNodeDependencies):

    _nodes_with_dependencies: Tuple[PipelineNode, ...]

    def __init__(self, nodes_with_dependencies: Tuple[PipelineNode, ...]):
        self._nodes_with_dependencies = nodes_with_dependencies

    def get_node_dependencies(self, node: PipelineNode) -> Tuple[PipelineNode, ...]:
        raise NotImplementedError()

    def get_nodes_with_dependencies(
            self, dependencies: Tuple[PipelineNode, ...]) -> Tuple[PipelineNode, ...]:
        return self._nodes_with_dependencies

    def register_node_dependencies(self, node: PipelineNode,
                                   dependencies: Tuple[PipelineNode, ...]) -> None:
        raise NotImplementedError()


class TestPromoteRegisteredNodesCommand:

    _registry: PipelineNodeStateClient
    _command: PromoteRegisteredNodesCommand

    def setup(self) -> None:
        self._registry = PipelineNodeStateClient()
        self._command = PromoteRegisteredNodesCommand(self._registry)

    def test_basics(self) -> None:
        node1 = PipelineNode("fake-1")
        node2 = PipelineNode("fake-2")

        self._registry.set_node_state(node1, PipelineNodeState.REGISTERED)
        self._registry.set_node_state(node2, PipelineNodeState.RUNNING)

        assert self._registry.get_node_state(node1) == PipelineNodeState.REGISTERED
        assert self._registry.get_node_state(node2) == PipelineNodeState.RUNNING
        self._command.execute()
        assert self._registry.get_node_state(node1) == PipelineNodeState.QUEUED
        assert self._registry.get_node_state(node2) == PipelineNodeState.RUNNING


class TestPromoteQueuedNodesCommand:

    _registry: PipelineNodeStateClient
    _command: PromoteQueuedNodesCommand

    def setup(self) -> None:
        node1 = PipelineNode("fake-1")
        node2 = PipelineNode("fake-2")
        self._registry = PipelineNodeStateClient()
        self._command = PromoteQueuedNodesCommand(
            state_client=self._registry,
            dependencies_client=FakeDependenciesClient(tuple([node1, node2]))
        )

    def test_basics(self) -> None:
        node1 = PipelineNode("fake-1")
        node2 = PipelineNode("fake-2")

        self._registry.set_node_state(node1, PipelineNodeState.QUEUED)
        self._registry.set_node_state(node2, PipelineNodeState.QUEUED)

        self._command.execute()
        assert self._registry.get_node_state(node1) == PipelineNodeState.PENDING
        assert self._registry.get_node_state(node2) == PipelineNodeState.PENDING


class FakeCommand(IExecutable):

    calls: int

    def __init__(self):
        self.calls = 0

    def execute(self) -> None:
        self.calls += 1


class TestOpenPipelineFrameCommand:

    _promote_registered: FakeCommand
    _promote_queued: FakeCommand
    _command: OpenPipelineFrameCommand

    def setup(self) -> None:
        self._promote_registered = FakeCommand()
        self._promote_queued = FakeCommand()
        self._command = OpenPipelineFrameCommand(self._promote_registered, self._promote_queued)

    def test_basics(self) -> None:
        assert self._promote_registered.calls == 0
        assert self._promote_queued.calls == 0
        self._command.execute()
        assert self._promote_registered.calls == 1
        assert self._promote_queued.calls == 1
