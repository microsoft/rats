from oneml.pipelines.session import (
    IPipelineSessionPlugin,
    IRegisterPipelineSessionPlugins,
    IActivatePipelineSessionPlugins,
    IManagePipelineSessionPlugins,
)


def test_imports() -> None:
    assert 1 == 1
