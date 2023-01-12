from abc import abstractmethod
from typing import TypedDict

import pytest

from oneml.processors import IProcess, Pipeline
from oneml.processors.ux import Task

StzEvalOut = TypedDict("StzEvalOut", {"Z": float})


class Standardize(IProcess):
    @abstractmethod
    def __init__(self, shift: float, scale: float) -> None:
        ...

    @abstractmethod
    def process(self, X: float) -> StzEvalOut:
        ...


@pytest.fixture
def stz() -> Pipeline:
    input_renames = {"X": "X.eval", "shift": "shift.eval", "scale": "scale.eval"}
    output_renames = {"Z": "Z.eval"}
    return Task(Standardize).rename_inputs(input_renames).rename_outputs(output_renames)


def test_single_incollection_subtract(stz: Pipeline) -> None:
    in_collection = stz.in_collections.X
    assert len(stz.in_collections.X) == 1

    # Tests InParameterCollection - Iterable[str]
    res = in_collection - ("eval",)
    assert len(res) == 0

    # Tests InParameterCollection - Iterable[InParameter]
    res = in_collection - (in_collection.eval,)
    assert len(res) == 0


def test_pipelineinput_subtract(stz: Pipeline) -> None:
    inputs = stz.in_collections
    assert len(inputs) == 3

    # Tests InParameterCollection - Iterable[str]
    res0 = inputs - ("X", "shift", "scale")
    res1 = inputs - ("X", "shift")
    res2 = inputs - ("X",)
    assert len(res0) == 0
    assert len(res1) == 1
    assert len(res2) == 2

    # Tests InParameterCollection - Iterable[str]
    res0 = inputs - ("X.eval", "shift", "scale")
    res1 = inputs - ("X.eval", "shift")
    res2 = inputs - ("X.eval",)
    assert len(res0) == 0
    assert len(res1) == 1
    assert len(res2) == 2

    # Tests InParameterCollection - Iterable[InParamCollection]
    res0 = inputs - (inputs.X, inputs.shift, inputs.scale)
    res1 = inputs - (inputs.X, inputs.shift)
    res2 = inputs - (inputs.X,)
    assert len(res0) == 0
    assert len(res1) == 1
    assert len(res2) == 2

    # Tests InParameterCollection - Iterable[InParameter]
    res0 = inputs - (inputs.X.eval, inputs.shift, inputs.scale)
    res1 = inputs - (inputs.X.eval, inputs.shift)
    res2 = inputs - (inputs.X.eval,)
    assert len(res0) == 0
    assert len(res1) == 1
    assert len(res2) == 2
