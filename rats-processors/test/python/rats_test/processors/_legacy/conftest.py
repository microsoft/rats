import logging
import shutil
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

from rats.app import RatsApp
from rats.processors._legacy.config import (
    PipelineConfigService,
    RatsProcessorsConfigServices,
)
from rats.processors._legacy.example._app_plugin import DiamondExampleDiContainer
from rats.processors._legacy.training import (
    IPersistFittedEvalPipeline,
    RatsProcessorsTrainingServices,
)
from rats.processors._legacy.ux import PipelineRunnerFactory, RatsProcessorsUxServices

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
def app() -> RatsApp:
    app = RatsApp.default()
    app.parse_service_container(DiamondExampleDiContainer(app))
    return app


@pytest.fixture(scope="package")
def pipeline_runner_factory(
    app: RatsApp,
) -> PipelineRunnerFactory:
    return app.get_service(RatsProcessorsUxServices.PIPELINE_RUNNER_FACTORY)


@pytest.fixture(scope="package")
def persist_fitted_eval_pipeline(
    app: RatsApp,
) -> IPersistFittedEvalPipeline:
    return app.get_service(RatsProcessorsTrainingServices.PERSIST_FITTED_EVAL_PIPELINE)


@pytest.fixture(scope="package")
def pipeline_config_service(app: RatsApp) -> PipelineConfigService:
    return app.get_service(RatsProcessorsConfigServices.PIPELINE_CONFIG_SERVICE)


@pytest.fixture(scope="package")
def register_resolvers_and_configs(pipeline_config_service: PipelineConfigService) -> None:
    return
