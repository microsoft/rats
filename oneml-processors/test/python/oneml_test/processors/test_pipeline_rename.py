from abc import abstractmethod
from typing import TypedDict

import pytest

from oneml.processors import Pipeline, PipelineBuilder, Task

StzTrainOut = TypedDict("StzTrainOut", {"mean": float, "scale": float, "Z": float})
StzEvalOut = TypedDict("StzEvalOut", {"Z": float})


class StandardizeTrain:
    @abstractmethod
    def process(self, X: float) -> StzTrainOut:
        ...


class StandardizeEval:
    @abstractmethod
    def __init__(self, mean: float, scale: float) -> None:
        ...

    @abstractmethod
    def process(self, X: float) -> StzEvalOut:
        ...


@pytest.fixture
def train_stz() -> Pipeline:
    return Task(StandardizeTrain)


@pytest.fixture
def eval_stz() -> Pipeline:
    return Task(StandardizeEval)


@pytest.fixture
def stz(train_stz: Pipeline, eval_stz: Pipeline) -> Pipeline:
    return PipelineBuilder.combine(
        train_stz,
        eval_stz,
        name="stz",
        dependencies=(
            eval_stz.inputs.mean << train_stz.outputs.mean,
            eval_stz.inputs.scale << train_stz.outputs.scale,
        ),
        inputs={"X.train": train_stz.inputs.X, "X.eval": eval_stz.inputs.X},
        outputs={"Z.train": train_stz.outputs.Z, "Z.eval": eval_stz.outputs.Z},
    )


def test_IOCollections_rename(train_stz: Pipeline) -> None:
    # InEntry -> InEntry
    pipeline1 = train_stz.rename_inputs({"X": "X0"})
    assert train_stz.inputs.X == pipeline1.inputs.X0

    # InEntry -> Inputs.InEntry
    pipeline1 = train_stz.rename_inputs({"X": "X.train"})
    assert train_stz.inputs.X == pipeline1.in_collections.X.train

    # Inputs.InEntry -> Inputs.InEntry
    pipeline2 = pipeline1.rename_inputs({"X.train": "X0.train0"})
    assert pipeline1.in_collections.X.train == pipeline2.in_collections.X0.train0

    # Inputs.InEntry -> InEntry
    pipeline2 = pipeline1.rename_inputs({"X.train": "X"})
    assert pipeline1.in_collections.X.train == pipeline2.inputs.X

    # OutEntry -> OutEntry
    pipeline1 = train_stz.rename_outputs({"Z": "Z0"})
    assert train_stz.outputs.Z == pipeline1.outputs.Z0

    # OutEntry -> Outputs.OutEntry
    pipeline1 = train_stz.rename_outputs({"Z": "Z.train"})
    assert train_stz.outputs.Z == pipeline1.out_collections.Z.train

    # Outputs.OutEntry -> Outputs.OutEntry
    pipeline2 = pipeline1.rename_outputs({"Z.train": "Z0.train0"})
    assert pipeline1.out_collections.Z.train == pipeline2.out_collections.Z0.train0

    # Outputs.OutEntry -> OutEntry
    pipeline2 = pipeline1.rename_outputs({"Z.train": "Z"})
    assert pipeline1.out_collections.Z.train == pipeline2.outputs.Z


def test_IOCollections_rename_and_merge_with_multiple_entries(stz: Pipeline) -> None:
    # Inputs.InEntry -> Inputs.InEntry
    pipeline1 = stz.rename_inputs({"X.train": "X0.train0"})
    assert stz.in_collections.X.train == pipeline1.in_collections.X0.train0
    assert stz.in_collections.X.eval == pipeline1.in_collections.X.eval

    # Inputs.InEntry -> InEntry
    pipeline1 = stz.rename_inputs({"X.train": "X0"})
    assert stz.in_collections.X.train == pipeline1.inputs.X0
    assert stz.in_collections.X.eval == pipeline1.in_collections.X.eval

    # InEntry -> InEntry
    pipeline2 = pipeline1.rename_inputs({"X0": "X1"})
    assert pipeline1.inputs.X0 == pipeline2.inputs.X1
    assert pipeline1.in_collections.X.eval == pipeline2.in_collections.X.eval

    # InEntry -> Inputs.InEntry
    pipeline2 = pipeline1.rename_inputs({"X0": "X.train"})
    assert stz.in_collections.X.train == pipeline2.in_collections.X.train
    assert pipeline1.in_collections.X.eval == pipeline2.in_collections.X.eval

    # InEntry | Inputs.InEntry
    pipeline2 = pipeline1.rename_inputs({"X0": "X.eval"})
    assert set(pipeline2.in_collections.X.eval) == set(
        stz.in_collections.X.train | stz.in_collections.X.eval
    )

    # Inputs.InEntry | InEntry
    pipeline2 = pipeline1.rename_inputs({"X.eval": "X0"})
    assert set(pipeline2.inputs.X0) == set(stz.in_collections.X.train | stz.in_collections.X.eval)

    # InEntry | InEntry
    pipeline2 = pipeline1.rename_inputs({"X.eval": "X1"})
    pipeline2 = pipeline2.rename_inputs({"X1": "X0"})
    assert set(pipeline2.inputs.X0) == set(stz.in_collections.X.train | stz.in_collections.X.eval)

    # Inputs.InEntry | Inputs.InEntry
    pipeline2 = stz.rename_inputs({"X.eval": "X.train"})
    assert set(pipeline2.in_collections.X.train) == set(
        stz.in_collections.X.train | stz.in_collections.X.eval
    )

    # Outputs.OutEntry -> Outputs.OutEntry
    pipeline1 = stz.rename_outputs({"Z.train": "Z0.train0"})
    assert stz.out_collections.Z.train == pipeline1.out_collections.Z0.train0
    assert stz.out_collections.Z.eval == pipeline1.out_collections.Z.eval

    # Outputs.OutEntry -> OutEntry
    pipeline1 = stz.rename_outputs({"Z.train": "Z0"})
    assert stz.out_collections.Z.train == pipeline1.outputs.Z0
    assert stz.out_collections.Z.eval == pipeline1.out_collections.Z.eval

    # OutEntry -> OutEntry
    pipeline2 = pipeline1.rename_outputs({"Z0": "Z1"})
    assert pipeline1.outputs.Z0 == pipeline2.outputs.Z1
    assert pipeline1.out_collections.Z.eval == pipeline2.out_collections.Z.eval

    # OutEntry -> Outputs.OutEntry
    pipeline2 = pipeline1.rename_outputs({"Z0": "Z.train"})
    assert stz.out_collections.Z.train == pipeline2.out_collections.Z.train
    assert pipeline1.out_collections.Z.eval == pipeline2.out_collections.Z.eval

    # OutEntry | Outputs.OutEntry
    pipeline2 = pipeline1.rename_outputs({"Z0": "Z.eval"})
    assert set(pipeline2.out_collections.Z.eval) == set(
        stz.out_collections.Z.train | stz.out_collections.Z.eval
    )

    # Outputs.OutEntry | OutEntry
    pipeline2 = pipeline1.rename_outputs({"Z.eval": "Z0"})
    assert set(pipeline2.outputs.Z0) == set(
        stz.out_collections.Z.train | stz.out_collections.Z.eval
    )

    # OutEntry | OutEntry
    pipeline2 = pipeline1.rename_outputs({"Z.eval": "Z1"})
    pipeline2 = pipeline2.rename_outputs({"Z1": "Z0"})
    assert set(pipeline2.outputs.Z0) == set(
        stz.out_collections.Z.train | stz.out_collections.Z.eval
    )

    # Outputs.OutEntry | Outputs.OutEntry
    pipeline2 = stz.rename_outputs({"Z.eval": "Z.train"})
    assert set(pipeline2.out_collections.Z.train) == set(
        stz.out_collections.Z.train | stz.out_collections.Z.eval
    )