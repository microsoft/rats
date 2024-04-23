from abc import abstractmethod
from itertools import chain
from typing import TypedDict

import pytest

from rats.processors._legacy.dag import IProcess
from rats.processors._legacy.ux import Dependency, UPipeline, UPipelineBuilder


class StzTrainOut(TypedDict):
    shift: float
    scale: float
    Z: float


class StzEvalOut(TypedDict):
    Z: float


class StandardizeTrain:
    @abstractmethod
    def process(self, X: float) -> StzTrainOut: ...


class StandardizeEval(IProcess):
    @abstractmethod
    def __init__(self, shift: float, scale: float) -> None: ...

    @abstractmethod
    def process(self, X: float) -> StzEvalOut: ...


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
        eval_stz.inputs.shift >> train_stz.outputs.shift  # type: ignore[operator]

    # Tests InParameter << OutParameter assignament
    dp = eval_stz.inputs.X.eval << train_stz.outputs.Z.train
    assert len(dp) == 1 and isinstance(dp[0], Dependency)

    with pytest.raises(TypeError):
        eval_stz.inputs.X.eval >> train_stz.outputs.Z.train  # type: ignore[operator]

    # Tests Outputs >> Inputs assignments
    dp = train_stz.outputs.scale >> eval_stz.inputs.scale
    assert len(dp) == 1 and isinstance(dp[0], Dependency)

    with pytest.raises(TypeError):
        train_stz.outputs.scale << eval_stz.inputs.scale  # type: ignore[operator]

    # Tests OutParameter >> InParameter assignments
    dp = train_stz.outputs.Z.train >> eval_stz.inputs.X.eval
    assert len(dp) == 1 and isinstance(dp[0], Dependency)

    with pytest.raises(TypeError):
        train_stz.outputs.Z.train << eval_stz.inputs.X.eval  # type: ignore[operator]


def test_mixed_UPipelineparams_assignments(train_stz: UPipeline, eval_stz: UPipeline) -> None:
    with pytest.raises(TypeError):  # not supported
        eval_stz.inputs.X << train_stz.outputs.shift

    with pytest.raises(TypeError):  # not supported
        train_stz.outputs.shift >> eval_stz.inputs.X

    with pytest.raises(TypeError):  # not supported
        eval_stz.inputs.shift << train_stz.outputs.Z

    with pytest.raises(TypeError):  # not supported
        train_stz.outputs.Z >> eval_stz.inputs.shift


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
    dps = stz2.inputs.X << stz1.outputs.Z
    assert len(dps) == 2 and all(isinstance(dp, Dependency) for dp in dps)

    with pytest.raises(TypeError):
        stz2.inputs.X >> stz1.outputs.Z  # type: ignore[operator]

    # Tests InParameter << OutParameter assignments
    dp1 = stz2.inputs.X.train << stz1.outputs.Z.train
    dp2 = stz2.inputs.X.eval << stz1.outputs.Z.eval
    assert len(dp1) == 1 and isinstance(dp1[0], Dependency)
    assert len(dp2) == 1 and isinstance(dp2[0], Dependency)

    with pytest.raises(TypeError):
        stz2.inputs.X.train >> stz1.outputs.Z.train  # type: ignore[operator]
        stz2.inputs.X.eval >> stz1.outputs.Z.eval  # type: ignore[operator]

    # Tests Outputs >> Inputs assignments
    dps = stz1.outputs.Z >> stz2.inputs.X
    assert len(dps) == 2 and all(isinstance(dp, Dependency) for dp in dps)

    with pytest.raises(TypeError):
        stz1.outputs.Z << stz2.inputs.X  # type: ignore[operator]

    # Tests OutParameter >> InParameter assignments
    dp1 = stz1.outputs.Z.train >> stz2.inputs.X.train
    dp2 = stz1.outputs.Z.eval >> stz2.inputs.X.eval
    assert len(dp1) == 1 and isinstance(dp1[0], Dependency)
    assert len(dp2) == 1 and isinstance(dp2[0], Dependency)

    with pytest.raises(TypeError):
        stz1.outputs.Z.train << stz1.inputs.X.train  # type: ignore[operator]
        stz1.outputs.Z.eval << stz1.inputs.X.eval  # type: ignore[operator]


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
        train_stz.outputs << eval_stz.inputs  # type: ignore[operator]

    # Test OutCollections >> InCollections
    dps = train_stz.outputs >> eval_stz.inputs
    assert len(dps) == 2 and all(isinstance(dp, Dependency) for dp in dps)
    assert dependencies == set(dps)

    with pytest.raises(TypeError):
        train_stz.inputs >> eval_stz.outputs  # type: ignore[operator]


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
