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
    PipelineRunner,
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
        shared_params=(
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
        shared_params=(model_eval.inputs.model << model_train.outputs.model,),
    )
    return e


#######

# STANDARDIZED LR PIPELINE


@pytest.fixture
def standardized_lr(standardization: Pipeline, logistic_regression: Pipeline) -> Pipeline:
    e = CombinedPipeline(
        standardization,
        logistic_regression,
        inputs={"X": standardization.inputs.X, "Y": logistic_regression.inputs.Y},
        outputs={
            "mean": standardization.outputs.mean.train,
            "scale": standardization.outputs.scale,
            "model": logistic_regression.outputs.model.train,
            "probs.train": logistic_regression.outputs.probs.train,
            "probs.eval": logistic_regression.outputs.probs.eval,
            "acc": logistic_regression.outputs.acc,
        },
        dependencies=(logistic_regression.inputs.X << standardization.outputs.Z,),
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
    call_log: defaultdict[str, int],
    standardized_lr: Pipeline,
    params_registry: ParamsRegistry,
) -> None:
    assert len(call_log) == 0
    runner = PipelineRunner(standardized_lr, params_registry)
    outputs = runner(
        name="pl",
        train_inputs=dict(X=ArrayMock("X1"), Y=ArrayMock("Y1")),
        eval_inputs=dict(X=ArrayMock("X2"), Y=ArrayMock("Y2")),
    )
    # assert len(call_log) == 2
    # assert call_log["spark"] == 1
    # assert call_log["wb_logger"] == 1
    assert set(outputs) == set(("mean", "scale", "model", "probs", "acc"))
    assert str(outputs["mean"]) == "mean(X1)"
    assert str(outputs["scale"]) == "scale(X1)"
    assert str(outputs["model"]) == "Model((X1-mean(X1))/scale(X1) ; Y1)"
    assert (
        str(outputs["probs"]["/pl/standardized_lr/logistic_regression/eval/ModelEval"])
        == "Model((X1-mean(X1))/scale(X1) ; Y1).probs((X2-mean(X1))/scale(X1))"
    )
    assert (
        str(outputs["acc"])
        == "acc(Model((X1-mean(X1))/scale(X1) ; Y1).probs((X2-mean(X1))/scale(X1)), Y2)"
    )
    assert (
        str(outputs["probs"]["/pl/standardized_lr/logistic_regression/train/ModelTrain"])
        == "Model((X1-mean(X1))/scale(X1) ; Y1).probs((X1-mean(X1))/scale(X1))"
    )


def test_single_output_multiple_input(
    standardized_lr: Pipeline, report1: Pipeline, report2: Pipeline
) -> None:
    reports = CombinedPipeline(
        report1,
        report2,
        name="reports",
        inputs={"acc._report1": report1.inputs.acc, "acc._report2": report2.inputs.acc},
    )
    pl = CombinedPipeline(
        standardized_lr,
        reports,
        name="pl",
        dependencies=(reports.inputs.acc << standardized_lr.outputs.acc,),
    )
    assert len(pl.inputs) == 2
    assert len(pl.outputs) == 4


# Fails on devops b/c the graphviz binary is not available.
# TODO: install graphviz on build machines?
# def test_viz(standardized_lr: Pipeline) -> None:
#     pipeline_to_svg(standardized_lr)
