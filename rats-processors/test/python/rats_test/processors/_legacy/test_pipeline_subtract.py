from abc import abstractmethod
from typing import TypedDict

import pytest

from rats.processors._legacy.dag import IProcess
from rats.processors._legacy.ux import UPipeline, UTask


class StzEvalOut(TypedDict):
    Z: float


class Standardize(IProcess):
    @abstractmethod
    def __init__(self, shift: float, scale: float) -> None: ...

    @abstractmethod
    def process(self, X: float) -> StzEvalOut: ...


@pytest.fixture
def stz() -> UPipeline:
    input_renames = {"X": "X.eval", "shift": "shift.eval", "scale": "scale.eval"}
    output_renames = {"Z": "Z.eval"}
    return UTask(Standardize).rename_inputs(input_renames).rename_outputs(output_renames)


def test_single_incollection_subtract(stz: UPipeline) -> None:
    in_collection = stz.inputs.X
    assert len(stz.inputs.X) == 1

    # Tests InParameterCollection - Iterable[str]
    res = in_collection - ("eval",)
    assert len(res) == 0


def test_pipelineinput_subtract(stz: UPipeline) -> None:
    inputs = stz.inputs
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
