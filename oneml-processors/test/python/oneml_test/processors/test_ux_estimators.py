from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Callable, TypedDict

import pytest

from oneml.processors import (
    FitAndEvaluateBuilders,
    IProcess,
    IRegistryOfSingletonFactories,
    ParamsFromEnvironmentSingletonsContract,
    RegistryOfSingletonFactories,
    SingletonFactory,
    SingletonFactoryPromise,
    Workflow,
    WorkflowClient,
    WorkflowRunner,
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


class StandardizeTrain(IProcess):
    def __init__(self, sc: SparkClient) -> None:
        pass

    def process(self, X: ArrayMock) -> StandardizeTrainOutput:
        mean = ArrayMock(f"mean({X})")
        scale = ArrayMock(f"scale({X})")
        Z = ArrayMock(f"({X}-{mean})/{scale}")
        return StandardizeTrainOutput(
            {
                "mean": mean,
                "scale": scale,
                "Z": Z,
            }
        )


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
        return ModelTrainOutput({"model": ModelMock(X, Y)})


ModelEvalOutput = TypedDict("ModelEvalOutput", {"probs": ArrayMock, "acc": ArrayMock})


class ModelEval(IProcess):
    def __init__(self, model: ModelMock, wblogger: WBLogger, sp: SparkClient) -> None:
        self.model = model

    def process(self, X: ArrayMock, Y: ArrayMock) -> ModelEvalOutput:
        probs = ArrayMock(f"{self.model}.probs({X})")
        acc = ArrayMock(f"acc({probs}, {Y})")
        return {"probs": probs, "acc": acc}


########

# REGISTRY


class SparkClient:
    pass


class SparkFactoryPromise(SingletonFactoryPromise[SparkClient]):
    def __init__(self) -> None:
        super().__init__("spark", SparkClient)


class WBLogger:
    pass


class WBLoggerFactoryPromise(SingletonFactoryPromise[WBLogger]):
    def __init__(self) -> None:
        super().__init__("wb_logger", WBLogger)


@pytest.fixture
def call_log() -> defaultdict[str, int]:
    return defaultdict(int)


@pytest.fixture
def spark_factory(call_log: defaultdict[str, int]) -> Callable[[], SparkClient]:
    def f() -> SparkClient:
        call_log["spark"] += 1
        return SparkClient()

    return f


@pytest.fixture
def wblogger_factory(call_log: defaultdict[str, int]) -> Callable[[], WBLogger]:
    def f() -> WBLogger:
        call_log["wb_logger"] += 1
        return WBLogger()

    return f


@pytest.fixture
def registry_of_singleton_factories(
    spark_factory: Callable[[], SparkClient], wblogger_factory: Callable[[], WBLogger]
) -> IRegistryOfSingletonFactories:
    return RegistryOfSingletonFactories(
        [
            SingletonFactory(SparkFactoryPromise(), spark_factory),
            SingletonFactory(WBLoggerFactoryPromise(), wblogger_factory),
        ]
    )


########

# ESTIMATORS


@pytest.fixture
def standardization() -> Workflow:
    standardize_train = WorkflowClient.single_task(
        "train",
        StandardizeTrain,
        params_from_environment_contract=ParamsFromEnvironmentSingletonsContract(
            sc=SparkFactoryPromise()
        ),
    )
    standardize_eval = WorkflowClient.single_task("eval", StandardizeEval)
    e = FitAndEvaluateBuilders.build_when_fit_evaluates_on_train(
        "standardization",
        standardize_train,
        standardize_eval,
        (
            standardize_eval.sig.mean << standardize_train.ret.mean,
            standardize_eval.sig.scale << standardize_train.ret.scale,
        ),
    )
    return e


@pytest.fixture
def logistic_regression() -> Workflow:
    model_train = WorkflowClient.single_task("train", ModelTrain)
    model_eval = WorkflowClient.single_task(
        "eval",
        ModelEval,
        params_from_environment_contract=ParamsFromEnvironmentSingletonsContract(
            wblogger=WBLoggerFactoryPromise(),
            sp=SparkFactoryPromise(),
        ),
    )

    e = FitAndEvaluateBuilders.build_when_fit_evaluates_on_train(
        "logistic_regression",
        model_train,
        model_eval,
        (model_eval.sig.model << model_train.ret.model,),
    )
    return e


#######

# STANDARDIZED LR WORKFLOW


@pytest.fixture
def standardized_lr(standardization: Workflow, logistic_regression: Workflow) -> Workflow:
    e = WorkflowClient.compose_workflow(
        "standardized_lr",
        (standardization, logistic_regression),
        (
            logistic_regression.sig.train_X << standardization.ret.train_Z,
            logistic_regression.sig.holdout_X << standardization.ret.holdout_Z,
        ),
        output_dependencies=(
            "mean" << standardization.ret.mean,
            "scale" << standardization.ret.scale,
            "model" << logistic_regression.ret.model,
            "holdout_probs" << logistic_regression.ret.holdout_probs,
            "holdout_acc" << logistic_regression.ret.holdout_acc,
        ),
    )
    return e


def test_standardized_lr(
    call_log: defaultdict[str, int],
    standardized_lr: Workflow,
    registry_of_singleton_factories: IRegistryOfSingletonFactories,
) -> None:
    assert len(call_log) == 0
    runner = WorkflowRunner(standardized_lr, registry_of_singleton_factories)
    outputs = runner(
        train_X=ArrayMock("X1"),
        train_Y=ArrayMock("Y1"),
        holdout_X=ArrayMock("X2"),
        holdout_Y=ArrayMock("Y2"),
    )
    assert len(call_log) == 2
    assert call_log["spark"] == 1
    assert call_log["wb_logger"] == 1
    assert set(outputs) == set(("mean", "scale", "model", "holdout_probs", "holdout_acc"))
    assert str(outputs["mean"]) == "mean(X1)"
    assert str(outputs["scale"]) == "scale(X1)"
    assert str(outputs["model"]) == "Model((X1-mean(X1))/scale(X1) ; Y1)"
    assert (
        str(outputs["holdout_probs"])
        == "Model((X1-mean(X1))/scale(X1) ; Y1).probs((X2-mean(X1))/scale(X1))"
    )
    assert (
        str(outputs["holdout_acc"])
        == "acc(Model((X1-mean(X1))/scale(X1) ; Y1).probs((X2-mean(X1))/scale(X1)), Y2)"
    )


# #######

# # XVAL PIPELINE

# xval = XVal("xval", (stz_lr,), config={"num_folds": 3})


# #######

# # HPO PIPELINE

# hpo_without_xval = HPO("hpo_without_xval", (stz_lr,), search_space={})
# hpo_with_xval = HPO("hpo_with_xval", (xval,), search_space={})
