from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import TypedDict

import pytest

from oneml.processors import (
    CombinedPipeline,
    IProcess,
    ParamsRegistry,
    Pipeline,
    PipelineRunnerFactory,
    RegistryId,
    Task,
)
from oneml.processors.ml import Estimator


@dataclass
class ArrayMock(object):
    v: str

    def __repr__(self) -> str:
        return self.v


@dataclass
class ModelMock(object):
    x: ArrayMock
    y: ArrayMock

    def __repr__(self) -> str:
        return f"Model({self.x} ; {self.y})"


########

# PROCESSORS (aka they do stuff; aka almost transformers)

StandardizeTrainOutput = TypedDict(
    "StandardizeTrainOutput", {"mean": ArrayMock, "scale": ArrayMock, "Z": ArrayMock}
)


class StandardizeTrain:
    def process(self, X: ArrayMock) -> StandardizeTrainOutput:
        mean = ArrayMock(f"mean({X})")
        scale = ArrayMock(f"scale({X})")
        Z = ArrayMock(f"({X}-{mean})/{scale}")
        return StandardizeTrainOutput({"mean": mean, "scale": scale, "Z": Z})


StandardizeEvalOutput = TypedDict("StandardizeEvalOutput", {"Z": ArrayMock})


class StandardizeEval(IProcess):
    def __init__(self, mean: ArrayMock, scale: ArrayMock) -> None:
        self._mu = mean
        self._scale = scale

    def process(self, X: ArrayMock) -> StandardizeEvalOutput:
        Z = ArrayMock(f"({X}-{self._mu})/{self._scale}")
        return StandardizeEvalOutput({"Z": Z})


ModelTrainOutput = TypedDict("ModelTrainOutput", {"model": ModelMock, "probs": ArrayMock})


class ModelTrain(IProcess):
    def process(self, X: ArrayMock, Y: ArrayMock) -> ModelTrainOutput:
        model = ModelMock(X, Y)
        probs = ArrayMock(f"{model}.probs({X})")
        return ModelTrainOutput({"model": model, "probs": probs})


ModelEvalOutput = TypedDict("ModelEvalOutput", {"probs": ArrayMock, "acc": ArrayMock})


class ModelEval(IProcess):
    def __init__(self, model: ModelMock) -> None:  # wblogger: WBLogger, sp: SparkClient
        self.model = model

    def process(self, X: ArrayMock, Y: ArrayMock) -> ModelEvalOutput:
        probs = ArrayMock(f"{self.model}.probs({X})")
        acc = ArrayMock(f"acc({probs}, {Y})")
        return {"probs": probs, "acc": acc}


class ReportGenerator(IProcess):
    def process(self, acc: ArrayMock) -> None:
        ...


########

# REGISTRY


class SparkClient:
    pass


class WBLogger:
    pass


@pytest.fixture
def params_registry() -> ParamsRegistry:
    registry = ParamsRegistry()
    registry.add(RegistryId("spark_client", SparkClient), SparkClient())
    registry.add(RegistryId("wb_logger", WBLogger), WBLogger())
    return registry


@pytest.fixture
def call_log() -> defaultdict[str, int]:
    return defaultdict(int)


########

# ESTIMATORS


@pytest.fixture
def standardization() -> Pipeline:
    standardize_train = Task(StandardizeTrain)
    standardize_eval = Task(StandardizeEval)
    e = Estimator(
        name="standardization",
        train_pl=standardize_train,
        eval_pl=standardize_eval,
        dependencies=(
            standardize_eval.inputs.mean << standardize_train.outputs.mean,
            standardize_eval.inputs.scale << standardize_train.outputs.scale,
        ),
    )
    return e


@pytest.fixture
def logistic_regression() -> Pipeline:
    model_train = Task(ModelTrain)
    model_eval = Task(ModelEval)

    e = Estimator(
        name="logistic_regression",
        train_pl=model_train,
        eval_pl=model_eval,
        dependencies=(model_eval.inputs.model << model_train.outputs.model,),
    )
    return e


#######

# STANDARDIZED LR PIPELINE


@pytest.fixture
def standardized_lr(standardization: Pipeline, logistic_regression: Pipeline) -> Pipeline:
    e = CombinedPipeline(
        pipelines=[standardization, logistic_regression],
        inputs={"X": standardization.in_collections.X, "Y": logistic_regression.in_collections.Y},
        outputs={
            "mean": standardization.outputs.mean,
            "scale": standardization.outputs.scale,
            "model": logistic_regression.outputs.model,
            "probs.train": logistic_regression.out_collections.probs.train,
            "probs.eval": logistic_regression.out_collections.probs.eval,
            "acc": logistic_regression.outputs.acc,
        },
        dependencies=(logistic_regression.in_collections.X << standardization.out_collections.Z,),
        name="standardized_lr",
    )
    return e


@pytest.fixture
def report1() -> Pipeline:
    return Task(ReportGenerator, "report1")


@pytest.fixture
def report2() -> Pipeline:
    return Task(ReportGenerator, "report2")


def test_standardized_lr(
    pipeline_runner_factory: PipelineRunnerFactory,
    standardized_lr: Pipeline,
) -> None:
    runner = pipeline_runner_factory(standardized_lr)
    outputs = runner(
        inputs={
            "X.train": ArrayMock("X1"),
            "Y.train": ArrayMock("Y1"),
            "X.eval": ArrayMock("X2"),
            "Y.eval": ArrayMock("Y2"),
        }
    )
    assert set(outputs) == set(("mean", "scale", "model", "probs", "acc"))
    assert str(outputs.mean) == "mean(X1)"
    assert str(outputs.scale) == "scale(X1)"
    assert str(outputs.model) == "Model((X1-mean(X1))/scale(X1) ; Y1)"
    assert (
        str(outputs.probs.eval)
        == "Model((X1-mean(X1))/scale(X1) ; Y1).probs((X2-mean(X1))/scale(X1))"
    )
    assert (
        str(outputs.acc)
        == "acc(Model((X1-mean(X1))/scale(X1) ; Y1).probs((X2-mean(X1))/scale(X1)), Y2)"
    )
    assert (
        str(outputs.probs.train)
        == "Model((X1-mean(X1))/scale(X1) ; Y1).probs((X1-mean(X1))/scale(X1))"
    )


def test_single_output_multiple_input(
    standardized_lr: Pipeline, report1: Pipeline, report2: Pipeline
) -> None:
    reports = CombinedPipeline(
        pipelines=[report1, report2],
        name="reports",
        inputs={"acc": report1.inputs.acc | report2.inputs.acc},
    )
    pl = CombinedPipeline(
        pipelines=[standardized_lr, reports],
        name="pl",
        dependencies=(reports.inputs.acc << standardized_lr.outputs.acc,),
    )
    assert len(pl.inputs) == 0
    assert len(pl.in_collections) == 2
    assert len(pl.outputs) == 3
    assert len(pl.out_collections) == 1


def test_wiring_outputs(standardization: Pipeline, logistic_regression: Pipeline) -> None:
    e = CombinedPipeline(
        pipelines=[standardization, logistic_regression],
        name="standardized_lr",
        dependencies=(logistic_regression.in_collections.X << standardization.out_collections.Z,),
        outputs={
            "A.mean": standardization.outputs.mean,
            "A.scale": standardization.outputs.scale,
            "A.model": logistic_regression.outputs.model,
            "A.probs_train": logistic_regression.out_collections.probs.train,
            "A.probs_eval": logistic_regression.out_collections.probs.eval,
            "A.acc": logistic_regression.outputs.acc,
        },
    )

    assert len(e.out_collections) == 1 and tuple(e.out_collections) == ("A",)
    assert len(e.out_collections.A) == 6
    assert set(e.out_collections.A) == set(
        ("mean", "scale", "model", "probs_train", "probs_eval", "acc")
    )


# Fails on devops b/c the graphviz binary is not available.
# TODO: install graphviz on build machines?
# def test_viz(standardized_lr: Pipeline) -> None:
#     pipeline_to_svg(standardized_lr)

# test svg painting
# from oneml.processors.dag._viz import pipeline_to_dot

# svg = pipeline_to_dot(e).create(format="svg")
# with open("p.svg", "wb") as f:
#     f.write(svg)
