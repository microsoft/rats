import logging

import pytest
from hydra.core.config_store import ConfigStore

from oneml.app import OnemlApp
from oneml.processors import PipelineRunnerFactory
from oneml.processors.dag import PipelineSessionProvider
from oneml.processors.plugin import OnemlProcessorsServices
from oneml.processors.schemas import register_configs
from oneml.processors.ux import register_resolvers

logger = logging.getLogger(__name__)


@pytest.fixture(scope="package")
def app() -> OnemlApp:
    return OnemlApp.default()


@pytest.fixture(scope="package")
def pipeline_session_provider(
    app: OnemlApp,
) -> PipelineSessionProvider:
    return app.get_service(OnemlProcessorsServices.PIPELINE_SESSION_PROVIDER)


@pytest.fixture(scope="package")
def pipeline_runner_factory(
    app: OnemlApp,
) -> PipelineRunnerFactory:
    return app.get_service(OnemlProcessorsServices.PIPELINE_RUNNER_FACTORY)


@pytest.fixture(scope="package")
def register_resolvers_and_configs() -> None:
    register_configs(ConfigStore())
    register_resolvers()
