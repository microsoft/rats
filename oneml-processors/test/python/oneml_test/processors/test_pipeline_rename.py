from abc import abstractmethod
from typing import TypedDict

import pytest
from oneml.processors.ux import PipelineBuilder, UPipeline, UTask


class StzTrainOut(TypedDict):
    mean: float
    scale: float
    Z: float


class StzEvalOut(TypedDict):
    Z: float


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
    assert set(pipeline.inputs) == set(("X1", "X2"))
    assert set(pipeline.outputs) == set(("Z1", "Z2"))
    assert set(pipeline.inputs.X1) == set(("train0", "eval"))
    assert set(pipeline.inputs.X2) == set(("train0", "eval"))
    assert set(pipeline.outputs.Z1) == set(("train", "eval0"))
    assert set(pipeline.outputs.Z2) == set(("train", "eval0"))


def test_IOCollections_rename(train_stz: UPipeline) -> None:
    # InPort -> InPort
    pipeline1 = train_stz.rename_inputs({"X": "X0"})
    assert train_stz.inputs.X == pipeline1.inputs.X0

    # InPort -> Inputs.InPort
    pipeline1 = train_stz.rename_inputs({"X": "X.train"})
    assert train_stz.inputs.X == pipeline1.inputs.X.train

    # Inputs.InPort -> Inputs.InPort
    pipeline2 = pipeline1.rename_inputs({"X.train": "X0.train0"})
    assert pipeline1.inputs.X.train == pipeline2.inputs.X0.train0

    # Inputs.InPort -> InPort
    pipeline2 = pipeline1.rename_inputs({"X.train": "X"})
    assert pipeline1.inputs.X.train == pipeline2.inputs.X

    # OutPort -> OutPort
    pipeline1 = train_stz.rename_outputs({"Z": "Z0"})
    assert train_stz.outputs.Z == pipeline1.outputs.Z0

    # OutPort -> Outputs.OutPort
    pipeline1 = train_stz.rename_outputs({"Z": "Z.train"})
    assert train_stz.outputs.Z == pipeline1.outputs.Z.train

    # Outputs.OutPort -> Outputs.OutPort
    pipeline2 = pipeline1.rename_outputs({"Z.train": "Z0.train0"})
    assert pipeline1.outputs.Z.train == pipeline2.outputs.Z0.train0

    # Outputs.OutPort -> OutPort
    pipeline2 = pipeline1.rename_outputs({"Z.train": "Z"})
    assert pipeline1.outputs.Z.train == pipeline2.outputs.Z


def test_IOCollections_rename_and_merge_with_multiple_entries(stz: UPipeline) -> None:
    # Inputs.InPort -> Inputs.InPort
    pipeline1 = stz.rename_inputs({"X.train": "X0.train0"})
    assert stz.inputs.X.train == pipeline1.inputs.X0.train0
    assert stz.inputs.X.eval == pipeline1.inputs.X.eval

    # Inputs.InPort -> Inputs.InPort
    pipeline1 = stz.rename_inputs({"X.train": "X0.train0", "X.eval": "X0.eval0"})
    assert stz.inputs.X.train == pipeline1.inputs.X0.train0
    assert stz.inputs.X.eval == pipeline1.inputs.X0.eval0
    with pytest.raises(AttributeError):
        pipeline1.inputs.X

    # Inputs.InPort -> InPort
    pipeline1 = stz.rename_inputs({"X.train": "X0"})
    assert stz.inputs.X.train == pipeline1.inputs.X0
    assert stz.inputs.X.eval == pipeline1.inputs.X.eval

    # InPort -> InPort
    pipeline2 = pipeline1.rename_inputs({"X0": "X1"})
    assert pipeline1.inputs.X0 == pipeline2.inputs.X1
    assert pipeline1.inputs.X.eval == pipeline2.inputs.X.eval

    # InPort -> Inputs.InPort
    pipeline2 = pipeline1.rename_inputs({"X0": "X.train"})
    assert stz.inputs.X.train == pipeline2.inputs.X.train
    assert pipeline1.inputs.X.eval == pipeline2.inputs.X.eval

    # InPort | Inputs.InPort
    pipeline2 = pipeline1.rename_inputs({"X0": "X.eval"})
    assert set(pipeline2.inputs.X.eval) == set(stz.inputs.X.train | stz.inputs.X.eval)

    # Inputs.InPort | InPort
    pipeline2 = pipeline1.rename_inputs({"X.eval": "X0"})
    assert set(pipeline2.inputs.X0) == set(stz.inputs.X.train | stz.inputs.X.eval)

    # InPort | InPort
    pipeline2 = pipeline1.rename_inputs({"X.eval": "X1"})
    pipeline2 = pipeline2.rename_inputs({"X1": "X0"})
    assert set(pipeline2.inputs.X0) == set(stz.inputs.X.train | stz.inputs.X.eval)

    # Inputs.InPort | Inputs.InPort
    pipeline2 = stz.rename_inputs({"X.eval": "X.train"})
    assert set(pipeline2.inputs.X.train) == set(stz.inputs.X.train | stz.inputs.X.eval)

    # Outputs.OutPort -> Outputs.OutPort
    pipeline1 = stz.rename_outputs({"Z.train": "Z0.train0"})
    assert stz.outputs.Z.train == pipeline1.outputs.Z0.train0
    assert stz.outputs.Z.eval == pipeline1.outputs.Z.eval

    # Outputs.OutPort -> OutPort
    pipeline1 = stz.rename_outputs({"Z.train": "Z0"})
    assert stz.outputs.Z.train == pipeline1.outputs.Z0
    assert stz.outputs.Z.eval == pipeline1.outputs.Z.eval

    # OutPort -> OutPort
    pipeline2 = pipeline1.rename_outputs({"Z0": "Z1"})
    assert pipeline1.outputs.Z0 == pipeline2.outputs.Z1
    assert pipeline1.outputs.Z.eval == pipeline2.outputs.Z.eval

    # OutPort -> Outputs.OutPort
    pipeline2 = pipeline1.rename_outputs({"Z0": "Z.train"})
    assert stz.outputs.Z.train == pipeline2.outputs.Z.train
    assert pipeline1.outputs.Z.eval == pipeline2.outputs.Z.eval

    # This test shows a bug in the rename_outputs b/c the resulting pipeline has Z.eval fed by
    # two nodes, the node that originally fed Z.eval and the node that originally fed Z0:
    # # OutPort | Outputs.OutPort
    # pipeline2 = pipeline1.rename_outputs({"Z0": "Z.eval"})
    # assert set(pipeline2.outputs.Z.eval) == set(
    #     stz.outputs.Z.train | stz.outputs.Z.eval
    # )

    # This test shows a bug in the rename_outputs b/c the resulting pipeline has Z0 fed by
    # two nodes, the node that originally fed Z.eval and the node that originally fed Z0:
    # # Outputs.OutPort | OutPort
    # pipeline2 = pipeline1.rename_outputs({"Z.eval": "Z0"})
    # assert set(pipeline2.outputs.Z0) == set(
    #     stz.outputs.Z.train | stz.outputs.Z.eval
    # )

    # This test shows a bug in the rename_outputs b/c the resulting pipeline has Z0 fed by
    # two nodes, the node that originally fed Z.eval and the node that originally fed Z0:
    # # OutPort | OutPort
    # pipeline2 = pipeline1.rename_outputs({"Z.eval": "Z1"})
    # pipeline2 = pipeline2.rename_outputs({"Z1": "Z0"})
    # assert set(pipeline2.outputs.Z0) == set(
    #     stz.outputs.Z.train | stz.outputs.Z.eval
    # )

    # This test shows a bug in the rename_outputs b/c the resulting pipeline has Z.train fed by
    # two nodes, the node that originally fed Z.eval and the node that originally fed Z.train:
    # # Outputs.OutPort | Outputs.OutPort
    # pipeline2 = stz.rename_outputs({"Z.eval": "Z.train"})
    # assert set(pipeline2.outputs.Z.train) == set(
    #     stz.outputs.Z.train | stz.outputs.Z.eval
    # )
