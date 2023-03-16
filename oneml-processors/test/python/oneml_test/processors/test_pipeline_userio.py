from abc import abstractmethod
from dataclasses import dataclass
from typing import TypedDict

import pytest

from oneml.processors import CombinedPipeline, IProcess, Pipeline, Task


@dataclass
class Array:
    ...


class ReportGenerator(IProcess):
    @abstractmethod
    def process(self, acc: Array) -> None:
        ...


@pytest.fixture
def report1() -> Pipeline:
    return Task(ReportGenerator, "report1").rename_inputs({"acc": "acc.report1"})


@pytest.fixture
def report2() -> Pipeline:
    return Task(ReportGenerator, "report2").rename_inputs({"acc": "acc.report2"})


def test_sequence_inputs_to_single_output(report1: Pipeline, report2: Pipeline) -> None:
    # Inputs <- Inputs | Inputs
    reports = CombinedPipeline(
        pipelines=[report1, report2],
        name="reports",
        inputs={"acc": report1.in_collections.acc | report2.in_collections.acc},
    )
    assert len(reports.in_collections) == 1
    assert len(reports.in_collections.acc) == 2
    assert (
        reports.in_collections.acc.report1
        == report1.decorate("reports").in_collections.acc.report1
    )
    assert (
        reports.in_collections.acc.report2
        == report2.decorate("reports").in_collections.acc.report2
    )

    # Inputs <- InEntry
    reports = CombinedPipeline(
        pipelines=[report1, report2],
        name="reports",
        inputs={
            "acc.report1": report1.in_collections.acc.report1,
            "acc.report2": report2.in_collections.acc.report2,
        },
    )
    assert len(reports.in_collections) == 1
    assert len(reports.in_collections.acc) == 2
    assert (
        reports.in_collections.acc.report1
        == report1.decorate("reports").in_collections.acc.report1
    )
    assert (
        reports.in_collections.acc.report2
        == report2.decorate("reports").in_collections.acc.report2
    )

    # Inputs | InEntry -> raises ValueError
    with pytest.raises(ValueError):
        report1.in_collections.acc | report2.in_collections.acc.report2  # type: ignore[operator]

    # Inputs.InEntry <- InEntry | InEntry
    reports = CombinedPipeline(
        pipelines=[report1, report2],
        name="reports",
        inputs={"acc.r": report1.in_collections.acc.report1 | report2.in_collections.acc.report2},
    )
    assert len(reports.in_collections) == 1
    assert len(reports.in_collections.acc) == 1
    assert len(reports.in_collections.acc.r) == 2
    assert (
        reports.in_collections.acc.r
        == report1.decorate("reports").in_collections.acc.report1
        | report2.decorate("reports").in_collections.acc.report2
    )

    # Inputs.InEntry <- Inputs | Inputs
    reports = CombinedPipeline(
        pipelines=[report1, report2],
        name="reports",
        inputs={"acc.r": report1.in_collections.acc | report2.in_collections.acc},
    )
    assert len(reports.in_collections) == 1
    assert len(reports.in_collections.acc) == 1
    assert len(reports.in_collections.acc.r) == 2
    assert (
        reports.in_collections.acc.r
        == report1.decorate("reports").in_collections.acc.report1
        | report2.decorate("reports").in_collections.acc.report2
    )

    # InEntry <- InEntry | Inputs
    with pytest.raises(ValueError):
        report1.in_collections.acc.report1 | report2.in_collections.acc


AOutput = TypedDict("AOutput", {"z": str})
BOutput = TypedDict("BOutput", {"z": str})
COutput = TypedDict("COutput", {"z": str})


class AProcessor(IProcess):
    @abstractmethod
    def process(self, x: str) -> AOutput:
        ...


class BProcessor(IProcess):
    @abstractmethod
    def process(self, x: str) -> BOutput:
        ...


class CProcessor(IProcess):
    @abstractmethod
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
    return CombinedPipeline(pipelines=[ATrain, AEval], name="A")


@pytest.fixture
def B(BTrain: Pipeline) -> Pipeline:
    return CombinedPipeline(pipelines=[BTrain], name="B")


@pytest.fixture
def C(CTrain: Pipeline, CEval: Pipeline) -> Pipeline:
    return CombinedPipeline(pipelines=[CTrain, CEval], name="C")


@pytest.fixture
def ABC(A: Pipeline, B: Pipeline, C: Pipeline) -> Pipeline:
    return CombinedPipeline(
        pipelines=[A, B, C],
        name="ABC",
        dependencies=(
            # should we allow B.inputs.X << A.outputs.z when B.inputs.X is a strict subset of
            # A.outputs.z?
            # should we allow B.inputs.X << A.outputs.z.train when B.inputs.X is a singleton?
            B.inputs.x << A.outputs.z,
            C.inputs.x << A.outputs.z,
        ),
        outputs={
            "z_A": A.outputs.z,
            "z_B": B.outputs.z,
            "z_C": C.outputs.z,
            "z.A_eval": A.outputs.z,
            "z.B_train": B.outputs.z,
            "z.C_train": C.outputs.z,
            "z.C_eval": C.outputs.z,
        },
    )


def test_combine_inputs(A: Pipeline, B: Pipeline, C: Pipeline, ABC: Pipeline) -> None:
    assert set(ABC.inputs) == set(("x",))
    assert ABC.inputs.x == A.inputs.x.decorate("ABC")
    assert set(ABC.outputs) == set(("z_A", "z_B", "z_C"))
    assert set(ABC.out_collections) == set(("z"))
    assert ABC.outputs.z_A == A.outputs.z.decorate("ABC")
    assert ABC.outputs.z_B == B.outputs.z.decorate("ABC")
    assert ABC.outputs.z_C == C.outputs.z.decorate("ABC")
    assert set(ABC.out_collections.z) == set(("A_eval", "B_train", "C_eval", "C_train"))
    assert ABC.out_collections.z.A_eval == A.outputs.z.decorate("ABC")
    assert ABC.out_collections.z.C_eval == C.outputs.z.decorate("ABC")
    assert ABC.out_collections.z.B_train == B.outputs.z.decorate("ABC")
    assert ABC.out_collections.z.C_train == C.outputs.z.decorate("ABC")

    # InEntry <- InEntry | InEntry
    D = CombinedPipeline(
        pipelines=[B, C], name="D", inputs={"x": B.inputs.x | C.inputs.x}, outputs={}
    )
    assert D.inputs.x == (B.inputs.x | C.inputs.x).decorate("D")

    # Inputs.InEntry <- InEntry | InEntry
    D = CombinedPipeline(
        pipelines=[B, C],
        name="D",
        inputs={
            "x.train": B.inputs.x | C.inputs.x,
            "x.eval": C.inputs.x,
        },
        outputs={},
    )
    assert D.in_collections.x.train == (B.inputs.x | C.inputs.x).decorate("D")
    assert D.in_collections.x.eval == C.inputs.x.decorate("D")

    # InEntry <- Inputs | Inputs
    D = CombinedPipeline(
        pipelines=[B, C],
        name="D",
        inputs={
            "x": B.inputs.x | C.inputs.x,
        },
        outputs={},
    )
    assert D.inputs.x == (B.inputs.x | C.inputs.x).decorate("D")
