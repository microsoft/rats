from oneml.pipelines.dag import (
    ILocatePipelineNodeDependencies,
    IManagePipelineNodeDependencies,
    IRegisterPipelineNodeDependencies,
    NodeDependenciesRegisteredError,
    PipelineNodeDependenciesClient,
)


def test_imports() -> None:
    assert 1 == 1
