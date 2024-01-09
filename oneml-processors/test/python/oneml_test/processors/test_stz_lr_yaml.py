from pathlib import Path
from typing import TypedDict

from hydra import compose, initialize_config_dir
from hydra_zen import instantiate

from oneml.processors.ux import CombinedPipeline

CONF_PATH = Path("src/resources/pipelines")


class Model:
    pass


class StzTrainOutput(TypedDict):
    mean: float
    scale: float
    Z: float


class StzEvalOutput(TypedDict):
    Z: float


class LRTrainOutput(TypedDict):
    model: Model
    probs: float


class LREvalOutput(TypedDict):
    acc: float
    probs: float


class StzTrain:
    def process(self, X: float) -> StzTrainOutput:
        mean = 1.0
        scale = 2.0
        Z = 3.0
        return StzTrainOutput({"mean": mean, "scale": scale, "Z": Z})


class StzEval:
    def __init__(self, mean: float, scale: float) -> None:
        self._mu = mean
        self._scale = scale

    def process(self, X: float) -> StzEvalOutput:
        Z = 4.1
        return StzEvalOutput({"Z": Z})


class LRTrain:
    def process(self, X: float, Y: float) -> LRTrainOutput:
        model = Model()
        probs = 0.5
        return LRTrainOutput({"model": model, "probs": probs})


class LREval:
    def __init__(self, model: float) -> None:
        self._model = model

    def process(self, X: float, Y: float) -> LREvalOutput:
        acc = 0.8
        probs = 0.2
        return LREvalOutput({"acc": acc, "probs": probs})


def test_user_configs(register_resolvers_and_configs: None) -> None:
    with initialize_config_dir(
        config_dir=str(CONF_PATH.absolute()), job_name="test", version_base=None
    ):
        cfg = compose(config_name="pipeline_config", overrides=["+example=stz_lr"])
        p = instantiate(cfg.pipeline)
        assert isinstance(p, CombinedPipeline)
        a = instantiate(p._config.pipelines["stz"])
        b = instantiate(cfg.pipeline.pipelines.stz)
        assert a == b
