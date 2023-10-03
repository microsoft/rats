from __future__ import annotations

from typing import TypedDict

import pytest

from oneml.processors.dag import IProcess
from oneml.processors.training import IPersistFittedEvalPipeline, TrainAndEvalBuilders
from oneml.processors.ux import (
    CombinedPipeline,
    InCollection,
    InCollections,
    InEntry,
    Inputs,
    NoInputs,
    NoOutputs,
    OutCollection,
    OutCollections,
    OutEntry,
    Outputs,
    Pipeline,
    PipelineRunnerFactory,
    Task,
    UPipeline,
    UTask,
)

from .mock_data import Array, Model

########

# PROCESSORS (aka they do stuff; aka almost transformers)

StandardizeTrainOutput = TypedDict(
    "StandardizeTrainOutput", {"mean": Array, "scale": Array, "Z": Array}
)


class StandardizeTrain:
    def process(self, X: Array) -> StandardizeTrainOutput:
        mean = Array(f"mean({X})")
        scale = Array(f"scale({X})")
        Z = Array(f"({X}-{mean})/{scale}")
        return StandardizeTrainOutput({"mean": mean, "scale": scale, "Z": Z})


StandardizeEvalOutput = TypedDict("StandardizeEvalOutput", {"Z": Array})


class StandardizeEval(IProcess):
    def __init__(self, mean: Array, scale: Array) -> None:
        self._mu = mean
        self._scale = scale

    def process(self, X: Array) -> StandardizeEvalOutput:
        Z = Array(f"({X}-{self._mu})/{self._scale}")
        return StandardizeEvalOutput({"Z": Z})


ModelTrainOutput = TypedDict("ModelTrainOutput", {"model": Model})


class ModelTrain(IProcess):
    def process(self, X: Array, Y: Array) -> ModelTrainOutput:
        model = Model(X, Y)
        return ModelTrainOutput({"model": model})


ModelEvalOutput = TypedDict("ModelEvalOutput", {"probs": Array, "acc": Array})


class ModelEval(IProcess):
    def __init__(self, model: Model) -> None:
        self.model = model

    def process(self, X: Array, Y: Array) -> ModelEvalOutput:
        probs = Array(f"{self.model}.probs({X})")
        acc = Array(f"acc({probs}, {Y})")
        return {"probs": probs, "acc": acc}


class ReportGenerator(IProcess):
    def process(self, acc: Array) -> None:
        return


########

# ESTIMATORS


class StzTrainIn(Inputs):
    X: InEntry[Array]


class StzTrainOut(Outputs):
    mean: OutEntry[Array]
    scale: OutEntry[Array]
    Z: OutEntry[Array]


class StzEvalIn(Inputs):
    mean: InEntry[Array]
    scale: InEntry[Array]


class StzEvalOut(Outputs):
    Z: OutEntry[Array]


class TrainEvalArrayIn(InCollection[Array]):
    train: InEntry[Array]
    eval: InEntry[Array]


class TrainEvalArrayOut(OutCollection[Array]):
    train: OutEntry[Array]
    eval: OutEntry[Array]


class XIn(InCollections):
    X: TrainEvalArrayIn


class MeanScaleOut(Outputs):
    mean: OutEntry[Array]
    scale: OutEntry[Array]


class ZOut(OutCollections):
    Z: TrainEvalArrayOut


StzPipeline = Pipeline[NoInputs, MeanScaleOut, XIn, ZOut]


@pytest.fixture
def standardization() -> StzPipeline:
    standardize_train = Task[StzTrainIn, StzTrainOut](StandardizeTrain, name="train")
    standardize_eval = Task[StzEvalIn, StzEvalOut](StandardizeEval)
    return TrainAndEvalBuilders.build_when_train_also_evaluates(  # type: ignore[return-value]
        name="standardization",
        train_pl=standardize_train,
        eval_pl=standardize_eval,
        dependencies=(
            standardize_eval.inputs.mean << standardize_train.outputs.mean,
            standardize_eval.inputs.scale << standardize_train.outputs.scale,
        ),
    )


class XYIn(InCollections):
    X: TrainEvalArrayIn
    Y: TrainEvalArrayIn


class ModelOut(Outputs):
    model: OutEntry[Model]


class ProbsAccOut(OutCollections):
    probs: TrainEvalArrayOut
    acc: TrainEvalArrayOut


LrPipeline = Pipeline[NoInputs, ModelOut, XYIn, ProbsAccOut]


@pytest.fixture
def logistic_regression() -> LrPipeline:
    model_train = UTask(ModelTrain, name="train")
    model_eval = UTask(ModelEval)

    return TrainAndEvalBuilders.build_using_train_and_eval(  # type: ignore[return-value]
        name="logistic_regression",
        train_pl=model_train,
        eval_pl=model_eval,
    )


def mypy_static_checks(standardization: StzPipeline, logistic_regression: LrPipeline) -> None:
    """Does not run; used to test mypy static checks."""
    standardization.outputs.mean << logistic_regression.outputs.model  # type: ignore[operator]
    standardization.inputs.noreturn << logistic_regression.outputs.model  # type: ignore[operator]
    standardization.in_collections.X << logistic_regression.out_collections.acc  # ok
    standardization.in_collections.X << logistic_regression.out_collections.acc.train  # type: ignore[operator]
    logistic_regression.outputs.model >> standardization.in_collections.X  # type: ignore[operator]
    logistic_regression.outputs.model >> standardization.in_collections.X.train  # type: ignore[operator]
    standardization.outputs.mean >> standardization.in_collections.X.train  # ok


#######

# STANDARDIZED LR PIPELINE


class ModelMeanScaleOut(ModelOut, MeanScaleOut):
    pass


StzLrPipeline = Pipeline[NoInputs, ModelMeanScaleOut, XYIn, ProbsAccOut]


@pytest.fixture
def standardized_lr(
    standardization: StzPipeline, logistic_regression: LrPipeline
) -> StzLrPipeline:
    return CombinedPipeline(
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


class AccIn(Inputs):
    acc: InEntry[Array]


@pytest.fixture
def report1() -> Task[AccIn, NoOutputs]:
    return Task[AccIn, NoOutputs](ReportGenerator, "report1")


@pytest.fixture
def report2() -> Task[AccIn, NoOutputs]:
    return Task[AccIn, NoOutputs](ReportGenerator, "report2")


def test_standardized_lr(
    pipeline_runner_factory: PipelineRunnerFactory,
    standardized_lr: UPipeline,
) -> None:
    standardized_lr = TrainAndEvalBuilders.with_multiple_eval_inputs(
        standardized_lr, eval_names=("eval_1", "eval_2")
    )
    runner = pipeline_runner_factory(standardized_lr)
    outputs = runner(
        inputs={
            "X.train": Array("Xt"),
            "Y.train": Array("Yt"),
            "X.eval_1": Array("Xe1"),
            "Y.eval_1": Array("Ye1"),
            "X.eval_2": Array("Xe2"),
            "Y.eval_2": Array("Ye2"),
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


def test_standardized_lr_with_persistance(
    pipeline_runner_factory: PipelineRunnerFactory,
    persist_fitted_eval_pipeline: IPersistFittedEvalPipeline,
    standardized_lr: UPipeline,
    output_base_uri: str,
) -> None:
    standardized_lr = persist_fitted_eval_pipeline.with_persistance(standardized_lr)
    runner = pipeline_runner_factory(standardized_lr)
    outputs = runner(
        inputs={
            "output_base_uri": output_base_uri,
            "X.train": Array("Xt"),
            "Y.train": Array("Yt"),
            "X.eval": Array("Xe1"),
            "Y.eval": Array("Ye1"),
        }
    )
    assert set(outputs) == set(
        ("mean", "scale", "model", "probs", "acc", "fitted_eval_pipeline", "uris")
    )
    assert str(outputs.mean) == "mean(Xt)"
    assert str(outputs.scale) == "scale(Xt)"
    assert str(outputs.model) == "Model((Xt-mean(Xt))/scale(Xt) ; Yt)"
    assert (
        str(outputs.probs.train)
        == "Model((Xt-mean(Xt))/scale(Xt) ; Yt).probs((Xt-mean(Xt))/scale(Xt))"
    )
    assert (
        str(outputs.probs.eval)
        == "Model((Xt-mean(Xt))/scale(Xt) ; Yt).probs((Xe1-mean(Xt))/scale(Xt))"
    )
    assert (
        str(outputs.acc.train)
        == "acc(Model((Xt-mean(Xt))/scale(Xt) ; Yt).probs((Xt-mean(Xt))/scale(Xt)), Yt)"
    )
    assert (
        str(outputs.acc.eval)
        == "acc(Model((Xt-mean(Xt))/scale(Xt) ; Yt).probs((Xe1-mean(Xt))/scale(Xt)), Ye1)"
    )
    assert set(outputs.uris) == set(("fitted_eval_pipeline", "mean_0", "scale_0", "model_0"))
    eval_pipeline = outputs.fitted_eval_pipeline
    assert isinstance(eval_pipeline, Pipeline)
    runner = pipeline_runner_factory(eval_pipeline)
    outputs = runner(
        inputs={
            "X.eval": Array("Xe2"),
            "Y.eval": Array("Ye2"),
        }
    )
    assert set(outputs) == set(("probs", "acc"))
    assert (
        str(outputs.probs.eval)
        == "Model((Xt-mean(Xt))/scale(Xt) ; Yt).probs((Xe2-mean(Xt))/scale(Xt))"
    )
    assert (
        str(outputs.acc.eval)
        == "acc(Model((Xt-mean(Xt))/scale(Xt) ; Yt).probs((Xe2-mean(Xt))/scale(Xt)), Ye2)"
    )


def test_single_output_multiple_input(
    standardized_lr: UPipeline, report1: Task[AccIn, NoOutputs], report2: Task[AccIn, NoOutputs]
) -> None:
    standardized_lr = TrainAndEvalBuilders.with_multiple_eval_inputs(
        standardized_lr, eval_names=("eval_1", "eval_2")
    )

    reports: UPipeline = CombinedPipeline(
        pipelines=[report1, report2],
        name="reports",
        inputs={"acc": report1.inputs.acc | report2.inputs.acc},
    )
    pl: UPipeline = CombinedPipeline(
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


def test_wiring_outputs(standardization: UPipeline, logistic_regression: UPipeline) -> None:
    standardization = TrainAndEvalBuilders.with_multiple_eval_inputs(
        standardization, eval_names=("eval_1", "eval_2")
    )
    logistic_regression = TrainAndEvalBuilders.with_multiple_eval_inputs(
        logistic_regression, eval_names=("eval_1", "eval_2")
    )
    e: UPipeline = CombinedPipeline(
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
# def test_viz(standardized_lr: UPipeline) -> None:
#     pipeline_to_svg(standardized_lr)

# test svg painting
# from oneml.processors.dag._viz import pipeline_to_dot

# svg = pipeline_to_dot(e).create(format="svg")
# with open("p.svg", "wb") as f:
#     f.write(svg)
