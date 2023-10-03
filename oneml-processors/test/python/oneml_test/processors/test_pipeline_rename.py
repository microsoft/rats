from abc import abstractmethod
from typing import Any, TypedDict

import pytest

from oneml.processors.ux import Pipeline, PipelineBuilder, UPipeline, UTask

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
def train_stz() -> UTask:
    return UTask(StandardizeTrain)


@pytest.fixture
def eval_stz() -> UTask:
    return UTask(StandardizeEval)


@pytest.fixture
def stz(train_stz: UPipeline, eval_stz: UPipeline) -> UPipeline:
    return PipelineBuilder.combine(
        pipelines=[train_stz, eval_stz],
        name="stz",
        dependencies=(
            eval_stz.inputs.mean << train_stz.outputs.mean,
            eval_stz.inputs.scale << train_stz.outputs.scale,
        ),
        inputs={"X.train": train_stz.inputs.X, "X.eval": eval_stz.inputs.X},
        outputs={"Z.train": train_stz.outputs.Z, "Z.eval": eval_stz.outputs.Z},
    )


@pytest.fixture
def double_stz(stz: UPipeline) -> UPipeline:
    stz1 = stz.decorate("stz1").rename_inputs({"X": "X1"}).rename_outputs({"Z": "Z1"})
    stz2 = stz.decorate("stz2").rename_inputs({"X": "X2"}).rename_outputs({"Z": "Z2"})
    return PipelineBuilder.combine(
        pipelines=[stz1, stz2],
        name="double_stz",
    )


def test_wildcard_rename(double_stz: UPipeline) -> None:
    pipeline = double_stz.rename_inputs({"*.train": "*.train0"}).rename_outputs(
        {"*.eval": "*.eval0"}
    )
    assert set(pipeline.inputs) == set()
    assert set(pipeline.outputs) == set()
    assert set(pipeline.in_collections) == set(("X1", "X2"))
    assert set(pipeline.out_collections) == set(("Z1", "Z2"))
    assert set(pipeline.in_collections.X1) == set(("train0", "eval"))
    assert set(pipeline.in_collections.X2) == set(("train0", "eval"))
    assert set(pipeline.out_collections.Z1) == set(("train", "eval0"))
    assert set(pipeline.out_collections.Z2) == set(("train", "eval0"))


def test_IOCollections_rename(train_stz: UPipeline) -> None:
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


def test_IOCollections_rename_and_merge_with_multiple_entries(stz: UPipeline) -> None:
    # Inputs.InEntry -> Inputs.InEntry
    pipeline1 = stz.rename_inputs({"X.train": "X0.train0"})
    assert stz.in_collections.X.train == pipeline1.in_collections.X0.train0
    assert stz.in_collections.X.eval == pipeline1.in_collections.X.eval

    # Inputs.InEntry -> Inputs.InEntry
    pipeline1 = stz.rename_inputs({"X.train": "X0.train0", "X.eval": "X0.eval0"})
    assert stz.in_collections.X.train == pipeline1.in_collections.X0.train0
    assert stz.in_collections.X.eval == pipeline1.in_collections.X0.eval0
    with pytest.raises(AttributeError):
        pipeline1.in_collections.X

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

    # This test shows a bug in the rename_outputs b/c the resulting pipeline has Z.eval fed by
    # two nodes, the node that originally fed Z.eval and the node that originally fed Z0:
    # # OutEntry | Outputs.OutEntry
    # pipeline2 = pipeline1.rename_outputs({"Z0": "Z.eval"})
    # assert set(pipeline2.out_collections.Z.eval) == set(
    #     stz.out_collections.Z.train | stz.out_collections.Z.eval
    # )

    # This test shows a bug in the rename_outputs b/c the resulting pipeline has Z0 fed by
    # two nodes, the node that originally fed Z.eval and the node that originally fed Z0:
    # # Outputs.OutEntry | OutEntry
    # pipeline2 = pipeline1.rename_outputs({"Z.eval": "Z0"})
    # assert set(pipeline2.outputs.Z0) == set(
    #     stz.out_collections.Z.train | stz.out_collections.Z.eval
    # )

    # This test shows a bug in the rename_outputs b/c the resulting pipeline has Z0 fed by
    # two nodes, the node that originally fed Z.eval and the node that originally fed Z0:
    # # OutEntry | OutEntry
    # pipeline2 = pipeline1.rename_outputs({"Z.eval": "Z1"})
    # pipeline2 = pipeline2.rename_outputs({"Z1": "Z0"})
    # assert set(pipeline2.outputs.Z0) == set(
    #     stz.out_collections.Z.train | stz.out_collections.Z.eval
    # )

    # This test shows a bug in the rename_outputs b/c the resulting pipeline has Z.train fed by
    # two nodes, the node that originally fed Z.eval and the node that originally fed Z.train:
    # # Outputs.OutEntry | Outputs.OutEntry
    # pipeline2 = stz.rename_outputs({"Z.eval": "Z.train"})
    # assert set(pipeline2.out_collections.Z.train) == set(
    #     stz.out_collections.Z.train | stz.out_collections.Z.eval
    # )
