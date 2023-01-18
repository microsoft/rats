from typing import Dict

from oneml.pipelines.dag import PipelineNode
from oneml.pipelines.session import DeferredExecutable, IExecutable, IExecutePipelineNodes


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

    def setup_method(self) -> None:
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
