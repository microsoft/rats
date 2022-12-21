from dataclasses import dataclass
from typing import TypedDict

import pytest

from oneml.processors import CombinedPipeline, IProcess, Pipeline, Task


@dataclass
class Array:
    ...


class ReportGenerator(IProcess):
    def process(self, acc: Array) -> None:
        ...


@pytest.fixture
def report1() -> Pipeline:
    return Task(ReportGenerator, "report1")


@pytest.fixture
def report2() -> Pipeline:
    return Task(ReportGenerator, "report2")


def test_sequence_inputs_to_single_output(report1: Pipeline, report2: Pipeline) -> None:
    # InCollection <- Sequence[InCollection, InCollection]
    reports = CombinedPipeline(
        report1,
        report2,
        name="reports",
        inputs={"acc": [report1.inputs.acc, report2.inputs.acc]},
    )
    assert len(reports.inputs) == 1
    assert len(reports.inputs.acc) == 2
    assert reports.inputs.acc.report1 == report1.decorate("reports").inputs.acc.report1
    assert reports.inputs.acc.report2 == report2.decorate("reports").inputs.acc.report2

    # InCollection <- Sequence[InCollectionEntry, InCollectionEntry]
    reports = CombinedPipeline(
        report1,
        report2,
        name="reports",
        inputs={"acc": [report1.inputs.acc.report1, report2.inputs.acc.report2]},
    )
    assert len(reports.inputs) == 1
    assert len(reports.inputs.acc) == 2
    assert reports.inputs.acc.report1 == report1.decorate("reports").inputs.acc.report1
    assert reports.inputs.acc.report2 == report2.decorate("reports").inputs.acc.report2

    # InCollection <- Sequence[InCollection, InCollectionEntry]
    reports = CombinedPipeline(
        report1,
        report2,
        name="reports",
        inputs={"acc": [report1.inputs.acc, report2.inputs.acc.report2]},
    )
    assert len(reports.inputs) == 1
    assert len(reports.inputs.acc) == 2
    assert reports.inputs.acc.report1 == report1.decorate("reports").inputs.acc.report1
    assert reports.inputs.acc.report2 == report2.decorate("reports").inputs.acc.report2

    # InCollectionEntry <- Sequence[InCollectionEntry, InCollectionEntry]
    reports = CombinedPipeline(
        report1,
        report2,
        name="reports",
        inputs={"acc.r": [report1.inputs.acc.report1, report2.inputs.acc.report2]},
    )
    assert len(reports.inputs) == 1
    assert len(reports.inputs.acc) == 1
    assert len(reports.inputs.acc.r) == 2
    assert (
        reports.inputs.acc.r
        == report1.decorate("reports").inputs.acc.report1
        | report2.decorate("reports").inputs.acc.report2
    )

    # InCollectionEntry <- Sequence[InCollection, InCollection]
    reports = CombinedPipeline(
        report1,
        report2,
        name="reports",
        inputs={"acc.r": [report1.inputs.acc, report2.inputs.acc]},
    )
    assert len(reports.inputs) == 1
    assert len(reports.inputs.acc) == 1
    assert len(reports.inputs.acc.r) == 2
    assert (
        reports.inputs.acc.r
        == report1.decorate("reports").inputs.acc.report1
        | report2.decorate("reports").inputs.acc.report2
    )

    # InCollectionEntry <- Sequence[InCollectionEntry, InCollection]
    reports = CombinedPipeline(
        report1,
        report2,
        name="reports",
        inputs={"acc.r": [report1.inputs.acc.report1, report2.inputs.acc]},
    )
    assert len(reports.inputs) == 1
    assert len(reports.inputs.acc) == 1
    assert len(reports.inputs.acc.r) == 2
    assert (
        reports.inputs.acc.r
        == report1.decorate("reports").inputs.acc.report1
        | report2.decorate("reports").inputs.acc.report2
    )


AOutput = TypedDict("AOutput", {"z": str})
BOutput = TypedDict("BOutput", {"z": str})
COutput = TypedDict("COutput", {"z": str})


class AProcessor(IProcess):
    def process(self, x: str) -> AOutput:
        ...


class BProcessor(IProcess):
    def process(self, x: str) -> BOutput:
        ...


class CProcessor(IProcess):
    def process(self, x: str) -> COutput:
        ...


@pytest.fixture
def ATrain() -> Pipeline:
    return Task(AProcessor, "train")


@pytest.fixture
def AEval() -> Pipeline:
    return Task(AProcessor, "eval")


@pytest.fixture
def BTrain() -> Pipeline:
    return Task(BProcessor, "train")


@pytest.fixture
def BEval() -> Pipeline:
    return Task(BProcessor, "eval")


@pytest.fixture
def CTrain() -> Pipeline:
    return Task(CProcessor, "train")


@pytest.fixture
def CEval() -> Pipeline:
    return Task(CProcessor, "eval")


@pytest.fixture
def A(ATrain: Pipeline, AEval: Pipeline) -> Pipeline:
    return CombinedPipeline(ATrain, AEval, name="A")


@pytest.fixture
def B(BTrain: Pipeline) -> Pipeline:
    return CombinedPipeline(BTrain, name="B")


@pytest.fixture
def C(CTrain: Pipeline, CEval: Pipeline) -> Pipeline:
    return CombinedPipeline(CTrain, CEval, name="C")


@pytest.fixture
def ABC(A: Pipeline, B: Pipeline, C: Pipeline) -> Pipeline:
    return CombinedPipeline(
        A,
        B,
        C,
        name="ABC",
        dependencies=(
            # should we allow B.inputs.X << A.outputs.z when B.inputs.X is a strict subset of
            # A.outputs.z?
            # should we allow B.inputs.X << A.outputs.z.train when B.inputs.X is a singleton?
            B.inputs.x.train << A.outputs.z.train,
            C.inputs.x << A.outputs.z,
        ),
        outputs={
            "z_A": A.outputs.z,
            "z_B": B.outputs.z,
            "z_C": C.outputs.z,
            "z.A_eval": A.outputs.z.eval,
            "z.B_train": B.outputs.z.train,
            "z.C_train": C.outputs.z.train,
            "z.C_eval": C.outputs.z.eval,
        },
    )


def test_combine_inputs(A: Pipeline, B: Pipeline, C: Pipeline, ABC: Pipeline) -> None:
    assert set(ABC.inputs) == set(("x",))
    assert ABC.inputs.x == A.inputs.x.decorate("ABC")
    assert set(ABC.outputs) == set(("z", "z_A", "z_B", "z_C"))
    assert ABC.outputs.z_A == A.outputs.z.decorate("ABC")
    assert ABC.outputs.z_B == B.outputs.z.decorate("ABC")
    assert ABC.outputs.z_C == C.outputs.z.decorate("ABC")
    assert set(ABC.outputs.z) == set(("A_eval", "B_train", "C_eval", "C_train"))
    assert ABC.outputs.z.A_eval == A.outputs.z.eval.decorate("ABC")
    assert ABC.outputs.z.C_eval == C.outputs.z.eval.decorate("ABC")
    assert ABC.outputs.z.B_train == B.outputs.z.train.decorate("ABC")
    assert ABC.outputs.z.C_train == C.outputs.z.train.decorate("ABC")

    # InCollection <- [InCollection, InCollection]
    D = CombinedPipeline(B, C, name="D", inputs={"x": [B.inputs.x, C.inputs.x]}, outputs={})
    assert D.inputs.x == (B.inputs.x | C.inputs.x).decorate("D")

    # InCollection <- [InCollectionEntry, InCollectionEntry]
    D = CombinedPipeline(
        B,
        C,
        name="D",
        inputs={
            "x.train": [B.inputs.x.train, C.inputs.x.train],
            "x.eval": [C.inputs.x.eval],
        },
        outputs={},
    )
    assert D.inputs.x == (B.inputs.x | C.inputs.x).decorate("D")

    # InCollectionEntry <- [InCollection, InCollection]
    D = CombinedPipeline(
        B,
        C,
        name="D",
        inputs={
            "x.mixed": [B.inputs.x, C.inputs.x],
        },
        outputs={},
    )
    bxtrain = B.inputs.x.rename({"train": "mixed"})
    cxtrain = C.inputs.x.rename({"train": "mixed"})
    cxeval = C.inputs.x.rename({"eval": "mixed"})
    assert D.inputs.x.mixed == (bxtrain | cxtrain | cxeval).mixed.decorate("D")
