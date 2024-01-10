from pathlib import Path
from typing import Any, TypedDict

import pytest
from hydra import compose, initialize_config_dir
from hydra_zen import instantiate

from oneml.app import OnemlApp
from oneml.processors.config import PipelineConfig
from oneml.processors.registry import IProvidePipelineCollection, OnemlProcessorsRegistryServices
from oneml.processors.ux import CombinedPipeline

CONF_PATH = Path("src/resources/pipelines")


class AOutput(TypedDict):
    Z1: float
    Z2: float


class BOutput(TypedDict):
    Z: float


class COutput(TypedDict):
    Z: float


DOutput = AOutput


class A:
    def process(self) -> AOutput:
        return {"Z1": 1.0, "Z2": 2.0}


class B:
    def process(self, X: Any) -> BOutput:
        return {"Z": 3.0}


class C:
    def process(self, X: Any) -> COutput:
        return {"Z": 4.0}


class D:
    def process(self, X1: Any, X2: Any) -> DOutput:
        return {"Z1": 5.0, "Z2": 6.0}


def test_user_configs(register_resolvers_and_configs: None) -> None:
    with initialize_config_dir(
        config_dir=str(CONF_PATH.absolute()), job_name="pytest", version_base=None
    ):
        cfg = compose(config_name="pipeline_config", overrides=["+example=diamond"])
        p = instantiate(cfg.pipeline)
        assert isinstance(p, CombinedPipeline)


@pytest.fixture
def pipeline_providers(app: OnemlApp) -> IProvidePipelineCollection:
    return app.get_service(OnemlProcessorsRegistryServices.PIPELINE_PROVIDERS)


def test_user_configs_with_providers(
    register_resolvers_and_configs: None,
    pipeline_providers: IProvidePipelineCollection,
) -> None:
    with initialize_config_dir(
        config_dir=str(CONF_PATH.absolute()), job_name="pytest", version_base=None
    ):
        cfg = compose(config_name="pipeline_config", overrides=["+example=two_diamonds"])
        instantiated_cfg: PipelineConfig = instantiate(cfg, pipeline_providers=pipeline_providers)
        assert instantiated_cfg.pipeline.name == "two_diamonds"
        assert set(instantiated_cfg.pipeline.inputs) == set()
        assert set(instantiated_cfg.pipeline.outputs) == set(("Z1", "Z2"))
