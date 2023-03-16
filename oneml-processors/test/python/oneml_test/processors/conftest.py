import pytest
from hydra.core.config_store import ConfigStore

from oneml.pipelines._client import SimplePipelineFactory
from oneml.pipelines.building import PipelineBuilderClient, PipelineBuilderFactory
from oneml.pipelines.context._client import IManageExecutionContexts
from oneml.pipelines.session import PipelineSessionClient
from oneml.processors import PipelineRunnerFactory
from oneml.processors.dag import PipelineSessionProvider
from oneml.processors.schemas import register_configs
from oneml.processors.ux import register_resolvers


class _PipelineBuilderFactory(PipelineBuilderFactory):
    def __init__(self, f: SimplePipelineFactory):
        self._f = f

    def get_instance(self) -> PipelineBuilderClient:
        return self._f.builder_client()

    def get_session_context(self) -> IManageExecutionContexts[PipelineSessionClient]:
        return self._f._pipeline_session_context()


@pytest.fixture
def pipeline_builder_factory() -> _PipelineBuilderFactory:
    return _PipelineBuilderFactory(SimplePipelineFactory())


@pytest.fixture
def pipeline_session_provider(
    pipeline_builder_factory: _PipelineBuilderFactory,
) -> PipelineSessionProvider:
    return PipelineSessionProvider(
        builder_factory=pipeline_builder_factory,
        session_context=pipeline_builder_factory.get_session_context(),
    )


@pytest.fixture
def pipeline_runner_factory(
    pipeline_session_provider: PipelineSessionProvider,
) -> PipelineRunnerFactory:
    return PipelineRunnerFactory(pipeline_session_provider=pipeline_session_provider)


@pytest.fixture(scope="package")
def register_resolvers_and_configs() -> None:
    register_configs(ConfigStore())
    register_resolvers()
