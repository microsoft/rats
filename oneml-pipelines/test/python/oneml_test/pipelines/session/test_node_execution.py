import pytest

from oneml.pipelines.dag import PipelineNode
from oneml.pipelines.session import PipelineNodeExecutablesClient, PipelineSession
from oneml.services import IExecutable


class _FakeExecutable(IExecutable):
    called: bool

    def __init__(self) -> None:
        self.called = False

    def execute(self) -> None:
        self.called = True


class TestPipelineNodeExecutablesClient:
    _client: PipelineNodeExecutablesClient

    def setup_method(self) -> None:
        self._client = PipelineNodeExecutablesClient(
            namespace=lambda: PipelineSession("fake"),
            node_ctx=lambda: PipelineNode("fake"),
        )

    def test_basics(self) -> None:
        executable = _FakeExecutable()
        node = PipelineNode("fake")

        self._client.set_executable(node, executable)

        assert executable == self._client.get_executable(node)

    def test_validation(self) -> None:
        executable1 = _FakeExecutable()
        executable2 = _FakeExecutable()

        node1 = PipelineNode("fake-1")
        node2 = PipelineNode("fake-2")

        self._client.set_executable(node1, executable1)

        with pytest.raises(RuntimeError):
            self._client.set_executable(node1, executable1)

        with pytest.raises(RuntimeError):
            self._client.set_executable(node1, executable2)

        with pytest.raises(RuntimeError):
            self._client.get_executable(node2)

    def test_execution(self) -> None:
        executable = _FakeExecutable()
        node = PipelineNode("fake")

        self._client.set_executable(node, executable)

        assert not executable.called
        self._client.execute_node(node)
        assert executable.called
