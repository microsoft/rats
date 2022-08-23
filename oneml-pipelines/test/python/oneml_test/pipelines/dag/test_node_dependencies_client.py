from oneml.pipelines.dag import (
    ILocatePipelineNodeDependencies,
    IRegisterPipelineNodeDependencies,
    IManagePipelineNodeDependencies,
    PipelineNodeDependenciesClient,
    NodeDependenciesRegisteredError,
)


def test_imports() -> None:
    assert 1 == 1
