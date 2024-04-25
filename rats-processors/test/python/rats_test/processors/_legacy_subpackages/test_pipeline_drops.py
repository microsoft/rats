from abc import abstractmethod
from typing import TypedDict

import pytest

from rats.processors._legacy_subpackages.ux import PipelineBuilder, UPipeline, UTask


class StzTrainOut(TypedDict):
    mean: float
    scale: float
    Z: float


class StzEvalOut(TypedDict):
    Z: float


class StandardizeTrain:
    @abstractmethod
    def process(self, X: float) -> StzTrainOut: ...


class StandardizeEval:
    @abstractmethod
    def __init__(self, mean: float, scale: float, optional: bool = False) -> None: ...

    @abstractmethod
    def process(self, X: float) -> StzEvalOut: ...


@pytest.fixture
def train_stz() -> UTask:
    return UTask(StandardizeTrain, "train")


@pytest.fixture
def eval_stz() -> UTask:
    return UTask(StandardizeEval, "eval")


@pytest.fixture
def stz(train_stz: UPipeline, eval_stz: UPipeline) -> UPipeline:
    return PipelineBuilder.combine(
        pipelines=[train_stz, eval_stz],
        name="stz",
        dependencies=(
            eval_stz.inputs.mean << train_stz.outputs.mean,
            eval_stz.inputs.scale << train_stz.outputs.scale,
        ),
        inputs={
            "X.train": train_stz.inputs.X,
            "X.eval": eval_stz.inputs.X,
            "optional": eval_stz.inputs.optional,
        },
        outputs={"Z.train": train_stz.outputs.Z, "Z.eval": eval_stz.outputs.Z},
    )


def test_drop_inputs(train_stz: UPipeline, eval_stz: UPipeline, stz: UPipeline) -> None:
    with pytest.raises(ValueError):
        train_stz.drop_inputs("X")

    p1 = eval_stz.drop_inputs("optional")
    assert "optional" not in p1.inputs

    p2 = stz.drop_inputs("optional")
    assert "optional" not in p2.inputs


def test_drop_outputs(train_stz: UPipeline, eval_stz: UPipeline, stz: UPipeline) -> None:
    p1 = train_stz.drop_outputs("mean", "scale")
    assert "mean" not in p1.outputs and "scale" not in p1.outputs

    p2 = train_stz.drop_outputs("Z")
    assert "Z" not in p2.outputs

    p3 = stz.drop_outputs("Z.train")
    assert "Z.train" not in p3.outputs
