import pytest

from oneml.pipelines.dag import PipelineNode
from oneml.pipelines.session import PipelineNodeExecutablesClient
from oneml.services import IExecutable


class FakeExecutable(IExecutable):
    called: bool

    def __init__(self) -> None:
        self.called = False

    def execute(self) -> None:
        self.called = True


class TestPipelineNodeExecutablesClient:
    _client: PipelineNodeExecutablesClient

    def setup_method(self) -> None:
        self._client = PipelineNodeExecutablesClient(lambda: 1)

    def test_basics(self) -> None:
        executable = FakeExecutable()
        node = PipelineNode("fake")

        self._client.set_executable(node, executable)

        assert executable == self._client.get_executable(node)

    def test_validation(self) -> None:
        executable1 = FakeExecutable()
        executable2 = FakeExecutable()

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
        executable = FakeExecutable()
        node = PipelineNode("fake")

        self._client.set_executable(node, executable)

        assert not executable.called
        self._client.execute_node(node)
        assert executable.called
