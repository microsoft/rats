import pytest
from hydra.core.config_store import ConfigStore

from oneml.pipelines._client import SimplePipelineFactory
from oneml.pipelines.building import IPipelineBuilderFactory
from oneml.pipelines.context._client import ContextClient
from oneml.pipelines.session import PipelineSessionClient, ServicesRegistry
from oneml.pipelines.session._session_client import PipelineSessionContext
from oneml.processors import PipelineRunnerFactory
from oneml.processors.dag import PipelineSessionProvider
from oneml.processors.schemas import register_configs
from oneml.processors.ux import register_resolvers


@pytest.fixture(scope="package")
def services_registry() -> ServicesRegistry:
    return ServicesRegistry()


@pytest.fixture(scope="package")
def pipeline_session_context() -> PipelineSessionContext:
    return ContextClient[PipelineSessionClient]()


@pytest.fixture(scope="package")
def pipeline_builder_factory(
    services_registry: ServicesRegistry,
    pipeline_session_context: PipelineSessionContext,
) -> IPipelineBuilderFactory:
    return SimplePipelineFactory(
        services=services_registry, session_context=pipeline_session_context
    )


@pytest.fixture(scope="package")
def pipeline_session_provider(
    pipeline_builder_factory: IPipelineBuilderFactory,
    pipeline_session_context: PipelineSessionContext,
) -> PipelineSessionProvider:
    return PipelineSessionProvider(
        builder_factory=pipeline_builder_factory,
        session_context=pipeline_session_context,
    )


@pytest.fixture(scope="package")
def pipeline_runner_factory(
    pipeline_session_provider: PipelineSessionProvider,
) -> PipelineRunnerFactory:
    return PipelineRunnerFactory(pipeline_session_provider=pipeline_session_provider)


@pytest.fixture(scope="package")
def register_resolvers_and_configs() -> None:
    register_configs(ConfigStore())
    register_resolvers()
