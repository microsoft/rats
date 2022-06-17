from oneml.pipelines import (
    IExecutable,
    ILocatePipelineNodeExecutables,
    LocalPipelineNodeExecutionContext,
    PipelineNode,
)


class FakeExecutable(IExecutable):
    called: bool

    def __init__(self):
        self.called = False

    def execute(self) -> None:
        self.called = True


mapping = {
    PipelineNode("node-1"): FakeExecutable(),
    PipelineNode("node-2"): FakeExecutable(),
    PipelineNode("node-3"): FakeExecutable(),
    PipelineNode("node-4"): FakeExecutable(),
}


class FakeExecutableLocator(ILocatePipelineNodeExecutables):

    def get_node_executable(self, node: PipelineNode) -> IExecutable:
        return mapping[node]


class TestLocalPipelineNodeExecutionContext:
    _context: LocalPipelineNodeExecutionContext

    def setup(self) -> None:
        self._context = LocalPipelineNodeExecutionContext(FakeExecutableLocator())

    def test_basics(self) -> None:
        assert mapping[PipelineNode("node-1")].called is False
        self._context.execute_node(PipelineNode("node-1"))
        assert mapping[PipelineNode("node-1")].called is True


class TestPipelineNodeExecutableRegistry:
    pass
