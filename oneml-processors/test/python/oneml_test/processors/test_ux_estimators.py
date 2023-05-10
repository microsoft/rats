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
    TrainAndEvalBuilders,
)


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


ModelTrainOutput = TypedDict("ModelTrainOutput", {"model": ModelMock})


class ModelTrain(IProcess):
    def process(self, X: ArrayMock, Y: ArrayMock) -> ModelTrainOutput:
        model = ModelMock(X, Y)
        return ModelTrainOutput({"model": model})


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
    standardize_train = Task(StandardizeTrain, name="train")
    standardize_eval = Task(StandardizeEval)
    e = TrainAndEvalBuilders.build_when_fit_evaluates_on_train(
        name="standardization",
        train_pl=standardize_train,
        eval_pl=standardize_eval,
        dependencies=(
            standardize_eval.inputs.mean << standardize_train.outputs.mean,
            standardize_eval.inputs.scale << standardize_train.outputs.scale,
        ),
        validation_names=set(("eval_1", "eval_2")),
    )
    return e


@pytest.fixture
def logistic_regression() -> Pipeline:
    model_train = Task(ModelTrain, name="train")
    model_eval = Task(ModelEval)

    e = TrainAndEvalBuilders.build_using_eval_on_train_and_eval(
        name="logistic_regression",
        train_pl=model_train,
        eval_pl=model_eval,
        validation_names=set(("eval_1", "eval_2")),
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
            "probs": logistic_regression.out_collections.probs,
            "acc": logistic_regression.out_collections.acc,
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
            "X.train": ArrayMock("Xt"),
            "Y.train": ArrayMock("Yt"),
            "X.eval_1": ArrayMock("Xe1"),
            "Y.eval_1": ArrayMock("Ye1"),
            "X.eval_2": ArrayMock("Xe2"),
            "Y.eval_2": ArrayMock("Ye2"),
        }
    )
    assert set(outputs) == set(("mean", "scale", "model", "probs", "acc"))
    assert str(outputs.mean) == "mean(Xt)"
    assert str(outputs.scale) == "scale(Xt)"
    assert str(outputs.model) == "Model((Xt-mean(Xt))/scale(Xt) ; Yt)"
    assert (
        str(outputs.probs.train)
        == "Model((Xt-mean(Xt))/scale(Xt) ; Yt).probs((Xt-mean(Xt))/scale(Xt))"
    )
    assert (
        str(outputs.probs.eval_1)
        == "Model((Xt-mean(Xt))/scale(Xt) ; Yt).probs((Xe1-mean(Xt))/scale(Xt))"
    )
    assert (
        str(outputs.probs.eval_2)
        == "Model((Xt-mean(Xt))/scale(Xt) ; Yt).probs((Xe2-mean(Xt))/scale(Xt))"
    )
    assert (
        str(outputs.acc.train)
        == "acc(Model((Xt-mean(Xt))/scale(Xt) ; Yt).probs((Xt-mean(Xt))/scale(Xt)), Yt)"
    )
    assert (
        str(outputs.acc.eval_1)
        == "acc(Model((Xt-mean(Xt))/scale(Xt) ; Yt).probs((Xe1-mean(Xt))/scale(Xt)), Ye1)"
    )
    assert (
        str(outputs.acc.eval_2)
        == "acc(Model((Xt-mean(Xt))/scale(Xt) ; Yt).probs((Xe2-mean(Xt))/scale(Xt)), Ye2)"
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
        dependencies=(reports.inputs.acc << standardized_lr.out_collections.acc.eval_1,),
    )
    assert set(pl.inputs) == set()
    assert set(pl.in_collections) == set(("X", "Y"))
    assert set(pl.in_collections.X) == set(("train", "eval_1", "eval_2"))
    assert set(pl.in_collections.Y) == set(("train", "eval_1", "eval_2"))
    assert set(pl.outputs) == set(("mean", "scale", "model"))
    assert set(pl.out_collections) == set(("probs", "acc"))
    assert set(pl.out_collections.probs) == set(("train", "eval_1", "eval_2"))
    assert set(pl.out_collections.acc) == set(("train", "eval_2"))


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
            "A.probs_eval": logistic_regression.out_collections.probs.eval_1,
            "A.acc": logistic_regression.out_collections.acc.eval_1,
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
