import pytest

from oneml.pipelines import IExecutable, PipelineNode, PipelineNodeExecutablesClient


class FakeExecutable(IExecutable):
    called: bool

    def __init__(self):
        self.called = False

    def execute(self) -> None:
        self.called = True


class TestPipelineNodeExecutablesClient:

    _client: PipelineNodeExecutablesClient

    def setup(self) -> None:
        self._client = PipelineNodeExecutablesClient()

    def test_basics(self) -> None:
        executable = FakeExecutable()
        node = PipelineNode("fake")

        self._client.register_node_executable(node, executable)

        assert executable == self._client.get_node_executable(node)

    def test_validation(self) -> None:
        executable1 = FakeExecutable()
        executable2 = FakeExecutable()

        node1 = PipelineNode("fake-1")
        node2 = PipelineNode("fake-2")

        self._client.register_node_executable(node1, executable1)

        with pytest.raises(RuntimeError):
            self._client.register_node_executable(node1, executable1)

        with pytest.raises(RuntimeError):
            self._client.register_node_executable(node1, executable2)

        with pytest.raises(RuntimeError):
            self._client.get_node_executable(node2)

    def test_execution(self) -> None:
        executable = FakeExecutable()
        node = PipelineNode("fake")

        self._client.register_node_executable(node, executable)

        assert not executable.called
        self._client.execute_node(node)
        assert executable.called
