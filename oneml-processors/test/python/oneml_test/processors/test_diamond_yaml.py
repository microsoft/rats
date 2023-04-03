from pathlib import Path
from typing import Any, TypedDict

from hydra import compose, initialize_config_dir
from hydra_zen import instantiate

from oneml.processors.ux import CombinedPipeline

CONF_PATH = Path("src/resources/conf")

AOutput = TypedDict("AOutput", {"Z1": float, "Z2": float})
BOutput = TypedDict("BOutput", {"Z": float})
COutput = TypedDict("COutput", {"Z": float})


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
    def process(self, X1: Any, X2: Any) -> None:
        pass


def test_user_configs(register_resolvers_and_configs: None) -> None:
    with initialize_config_dir(
        config_dir=str(CONF_PATH.absolute()), job_name="pytest", version_base=None
    ):
        cfg = compose(config_name="config", overrides=["+example=diamond"])
        res = instantiate(cfg)
        assert isinstance(res.pipeline, CombinedPipeline)