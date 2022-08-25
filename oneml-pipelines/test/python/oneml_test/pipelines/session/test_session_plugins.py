from oneml.pipelines.session import (
    IActivatePipelineSessionPlugins,
    IManagePipelineSessionPlugins,
    IPipelineSessionPlugin,
    IRegisterPipelineSessionPlugins,
)


def test_imports() -> None:
    assert 1 == 1
