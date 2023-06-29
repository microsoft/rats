import logging
import shutil
from pathlib import Path
from typing import Any, Iterator

import pytest
from hydra.core.config_store import ConfigStore

from oneml.app import OnemlApp
from oneml.processors import (
    IPersistFittedEvalPipeline,
    OnemlProcessorsServices,
    PipelineRunnerFactory,
)
from oneml.processors.dag import PipelineSessionProvider
from oneml.processors.schemas import register_configs
from oneml.processors.ux import register_resolvers

logger = logging.getLogger(__name__)


@pytest.fixture(scope="package", params=["memory", "disk"])
def _rw_location(request: pytest.FixtureRequest) -> str:
    return request.param


@pytest.fixture(scope="package")
def output_base_uri(
    _rw_location: str,
    tmpdir_factory: Any,
) -> Iterator[str]:
    if _rw_location == "memory":
        yield "memory://"
    elif _rw_location == "disk":
        tmp_path = Path(tmpdir_factory.mktemp(".tmp"))
        yield tmp_path.as_uri()
        shutil.rmtree(str(tmp_path))
    else:
        raise ValueError(f"Unknown rw_location: {_rw_location}")


@pytest.fixture(scope="package")
def app() -> OnemlApp:
    app = OnemlApp.default()
    return app


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
def persist_fitted_eval_pipeline(
    app: OnemlApp,
) -> IPersistFittedEvalPipeline:
    return app.get_service(OnemlProcessorsServices.PERSIST_FITTED_EVAL_PIPELINE)


@pytest.fixture(scope="package")
def register_resolvers_and_configs() -> None:
    register_configs(ConfigStore())
    register_resolvers()
