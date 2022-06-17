from typing import Dict

import pytest

from oneml.pipelines import (
    DeferredExecutable,
    IExecutable,
    IExecutePipelineNodes,
    PipelineNode,
    PipelineNodeExecutableRegistry,
    PipelineNodeExecutionClient,
)


class FakeExecutable(IExecutable):
    called: bool

    def __init__(self):
        self.called = False

    def execute(self) -> None:
        self.called = True


class FakeExecutionContext(IExecutePipelineNodes):

    execution_counts: Dict[PipelineNode, int]

    def __init__(self):
        self.execution_counts = {}

    def execute_node(self, node: PipelineNode) -> None:
        self.execution_counts[node] = self.execution_counts.get(node, 0) + 1


class TestDeferredExecutable:
    _callback_called: bool
    _fake_executable: FakeExecutable

    def setup(self) -> None:
        self._callback_called = False
        self._fake_executable = FakeExecutable()

    def test_basics(self) -> None:
        def callback() -> IExecutable:
            self._callback_called = True
            return self._fake_executable

        executable = DeferredExecutable(callback)
        assert self._callback_called is False
        assert self._fake_executable.called is False
        executable.execute()
        assert self._callback_called is True
        assert self._fake_executable.called is True


class TestPipelineNodeExecutableRegistry:

    _registry: PipelineNodeExecutableRegistry

    def setup(self) -> None:
        self._registry = PipelineNodeExecutableRegistry()

    def test_basics(self) -> None:
        executable = FakeExecutable()
        node = PipelineNode("fake")

        self._registry.register_node_executable(node, executable)

        assert executable == self._registry.get_node_executable(node)

    def test_validation(self) -> None:
        executable1 = FakeExecutable()
        executable2 = FakeExecutable()

        node1 = PipelineNode("fake-1")
        node2 = PipelineNode("fake-2")

        self._registry.register_node_executable(node1, executable1)

        with pytest.raises(RuntimeError):
            self._registry.register_node_executable(node1, executable1)

        with pytest.raises(RuntimeError):
            self._registry.register_node_executable(node1, executable2)

        with pytest.raises(RuntimeError):
            self._registry.get_node_executable(node2)


class TestPipelineNodeExecutionClient:

    _execution_context: FakeExecutionContext
    _client: PipelineNodeExecutionClient

    def setup(self) -> None:
        self._execution_context = FakeExecutionContext()
        self._client = PipelineNodeExecutionClient(
            execution_context=self._execution_context,
            # Should probably mock this for better test stability
            registry=PipelineNodeExecutableRegistry(),
        )

    def test_basics(self) -> None:
        executable = FakeExecutable()
        node = PipelineNode("fake")

        self._client.register_node_executable(node, executable)

        assert executable == self._client.get_node_executable(node)

    def test_execution(self) -> None:
        executable = FakeExecutable()
        node = PipelineNode("fake")

        self._client.register_node_executable(node, executable)

        assert node not in self._execution_context.execution_counts
        self._client.execute_node(node)
        assert self._execution_context.execution_counts[node] == 1
