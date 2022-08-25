from oneml.pipelines.building import (
    CallableMultiExecutable,
    ICallableMultiExecutable,
    IMultiplexPipelineNodes,
    MultiPipelineNodeExecutable,
    PipelineMultiplexValuesType,
    PipelineNodeMultiplexer,
    PipelineNodeMultiplexerFactory,
)


def test_imports() -> None:
    assert 1 == 1
