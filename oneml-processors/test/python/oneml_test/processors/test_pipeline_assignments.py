from abc import abstractmethod
from itertools import chain
from typing import TypedDict

import pytest

from oneml.processors.dag import IProcess
from oneml.processors.ux import Dependency, UPipeline, UPipelineBuilder

StzTrainOut = TypedDict("StzTrainOut", {"shift": float, "scale": float, "Z": float})
StzEvalOut = TypedDict("StzEvalOut", {"Z": float})


class StandardizeTrain:
    @abstractmethod
    def process(self, X: float) -> StzTrainOut:
        ...


class StandardizeEval(IProcess):
    @abstractmethod
    def __init__(self, shift: float, scale: float) -> None:
        ...

    @abstractmethod
    def process(self, X: float) -> StzEvalOut:
        ...


@pytest.fixture
def train_stz() -> UPipeline:
    return (
        UPipelineBuilder.task(StandardizeTrain)
        .rename_inputs({"X": "X.train"})
        .rename_outputs({"Z": "Z.train"})
    )


@pytest.fixture
def eval_stz() -> UPipeline:
    return (
        UPipelineBuilder.task(StandardizeEval)
        .rename_inputs({"X": "X.eval"})
        .rename_outputs({"Z": "Z.eval"})
    )


def test_single_UPipelineparams_assignments(train_stz: UPipeline, eval_stz: UPipeline) -> None:
    # Tests Inputs << Outputs assignments
    dp = eval_stz.inputs.shift << train_stz.outputs.shift
    assert len(dp) == 1 and isinstance(dp[0], Dependency)

    with pytest.raises(TypeError):
        eval_stz.inputs.shift >> train_stz.outputs.shift  # type: ignore

    # Tests InParameter << OutParameter assignament
    dp = eval_stz.in_collections.X.eval << train_stz.out_collections.Z.train
    assert len(dp) == 1 and isinstance(dp[0], Dependency)

    with pytest.raises(TypeError):
        eval_stz.in_collections.X.eval >> train_stz.out_collections.Z.train  # type: ignore

    # Tests Outputs >> Inputs assignments
    dp = train_stz.outputs.scale >> eval_stz.inputs.scale
    assert len(dp) == 1 and isinstance(dp[0], Dependency)

    with pytest.raises(TypeError):
        train_stz.outputs.scale << eval_stz.inputs.scale  # type: ignore

    # Tests OutParameter >> InParameter assignments
    dp = train_stz.out_collections.Z.train >> eval_stz.in_collections.X.eval
    assert len(dp) == 1 and isinstance(dp[0], Dependency)

    with pytest.raises(TypeError):
        train_stz.out_collections.Z.train << eval_stz.in_collections.X.eval  # type: ignore


def test_mixed_UPipelineparams_assignments(train_stz: UPipeline, eval_stz: UPipeline) -> None:
    with pytest.raises(ValueError):  # not supported
        eval_stz.in_collections.X << train_stz.outputs.shift  # type: ignore

    with pytest.raises(ValueError):  # not supported
        train_stz.outputs.shift >> eval_stz.in_collections.X  # type: ignore

    with pytest.raises(ValueError):  # not supported
        eval_stz.inputs.shift << train_stz.out_collections.Z  # type: ignore

    with pytest.raises(ValueError):  # not supported
        train_stz.out_collections.Z >> eval_stz.inputs.shift  # type: ignore


def test_collection_UPipelineparams_assignments(train_stz: UPipeline, eval_stz: UPipeline) -> None:
    stz1 = UPipelineBuilder.combine(
        pipelines=[train_stz, eval_stz],
        dependencies=(
            train_stz.outputs.shift >> eval_stz.inputs.shift,
            train_stz.outputs.scale >> eval_stz.inputs.scale,
        ),
        name="stz1",
    )
    stz2 = UPipelineBuilder.combine(
        pipelines=[train_stz, eval_stz],
        dependencies=(
            train_stz.outputs.shift >> eval_stz.inputs.shift,
            train_stz.outputs.scale >> eval_stz.inputs.scale,
        ),
        name="stz2",
    )

    # Tests Inputs << Outputs assignments
    dps = stz2.in_collections.X << stz1.out_collections.Z  # many to many
    assert len(dps) == 2 and all(isinstance(dp, Dependency) for dp in dps)

    with pytest.raises(TypeError):
        stz2.in_collections.X >> stz1.out_collections.Z  # type: ignore

    # Tests InParameter << OutParameter assignments
    dp1 = stz2.in_collections.X.train << stz1.out_collections.Z.train
    dp2 = stz2.in_collections.X.eval << stz1.out_collections.Z.eval
    assert len(dp1) == 1 and isinstance(dp1[0], Dependency)
    assert len(dp2) == 1 and isinstance(dp2[0], Dependency)

    with pytest.raises(TypeError):
        stz2.in_collections.X.train >> stz1.out_collections.Z.train  # type: ignore
        stz2.in_collections.X.eval >> stz1.out_collections.Z.eval  # type: ignore

    # Tests Outputs >> Inputs assignments
    dps = stz1.out_collections.Z >> stz2.in_collections.X  # many to many
    assert len(dps) == 2 and all(isinstance(dp, Dependency) for dp in dps)

    with pytest.raises(TypeError):
        stz1.out_collections.Z << stz2.in_collections.X  # type: ignore

    # Tests OutParameter >> InParameter assignments
    dp1 = stz1.out_collections.Z.train >> stz2.in_collections.X.train
    dp2 = stz1.out_collections.Z.eval >> stz2.in_collections.X.eval
    assert len(dp1) == 1 and isinstance(dp1[0], Dependency)
    assert len(dp2) == 1 and isinstance(dp2[0], Dependency)

    with pytest.raises(TypeError):
        stz1.out_collections.Z.train << stz1.in_collections.X.train  # type: ignore
        stz1.out_collections.Z.eval << stz1.in_collections.X.eval  # type: ignore


def test_IOCollections_assignments(train_stz: UPipeline, eval_stz: UPipeline) -> None:
    dependencies = set(
        chain(
            eval_stz.inputs.shift << train_stz.outputs.shift,
            eval_stz.inputs.scale << train_stz.outputs.scale,
        )
    )

    # Test InCollections << OutCollections
    dps = eval_stz.inputs << train_stz.outputs
    assert len(dps) == 2 and all(isinstance(dp, Dependency) for dp in dps)
    assert dependencies == set(dps)

    with pytest.raises(TypeError):
        train_stz.outputs << eval_stz.inputs  # type: ignore

    # Test OutCollections >> InCollections
    dps = train_stz.outputs >> eval_stz.inputs
    assert len(dps) == 2 and all(isinstance(dp, Dependency) for dp in dps)
    assert dependencies == set(dps)

    with pytest.raises(TypeError):
        train_stz.inputs >> eval_stz.outputs  # type: ignore


def test_UPipeline_assignments(train_stz: UPipeline, eval_stz: UPipeline) -> None:
    dependencies = set(eval_stz.inputs << train_stz.outputs)

    # Test UPipeline << UPipeline
    dps = eval_stz << train_stz
    assert len(dps) == 2 and all(isinstance(dp, Dependency) for dp in dps)
    assert dependencies == set(dps)

    dps = train_stz << eval_stz
    assert len(dps) == 0

    # Test UPipeline >> UPipeline
    dps = train_stz >> eval_stz
    assert len(dps) == 2 and all(isinstance(dp, Dependency) for dp in dps)
    assert dependencies == set(dps)

    dps = eval_stz >> train_stz
    assert len(dps) == 0
