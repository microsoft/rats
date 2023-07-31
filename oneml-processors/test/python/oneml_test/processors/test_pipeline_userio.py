from abc import abstractmethod
from dataclasses import dataclass
from typing import TypedDict

import pytest

from oneml.processors.dag import IProcess
from oneml.processors.ux import CombinedPipeline, Pipeline, Task


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


class SinkProcessor(IProcess):
    @abstractmethod
    def process(self, x: str) -> None:
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
def Sink() -> Pipeline:
    return Task(SinkProcessor, "sync")


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


def test_combine_outputs(ATrain: Pipeline, AEval: Pipeline, Sink: Pipeline) -> None:
    # This test shows a bug in the default mechanism for defining the outputs of CombinedPipeline.
    # The signatures of ATrain_AEval and of ATrain_duplicated are identical - both have a single
    # output collection - 'z', with two entries, 'a', and 'b'.
    # When combining ATrain_AEval with S2, using z.a in a dependency, we get the expected output
    # signature - z.b, because z.a was used and removed from the output signature.
    # But when combining ATrain_duplicated with S2, using z.a in a dependency, we get no output.
    S2 = CombinedPipeline(
        name="S2",
        pipelines=(Sink.decorate("S1"), Sink.decorate("S2"), Sink.decorate("S3")),
    )
    ATrain_AEval = CombinedPipeline(
        name="ATrain_AEval",
        pipelines=(ATrain, AEval),
        outputs={
            "z.a": ATrain.outputs.z,
            "z.b": AEval.outputs.z,
        },
    )
    assert set(ATrain_AEval.outputs) == set()
    assert set(ATrain_AEval.out_collections) == set(("z",))
    assert set(ATrain_AEval.out_collections.z) == set(("a", "b"))
    ATrain_AEval_S2 = CombinedPipeline(
        name="ATrain_AEval_S2",
        pipelines=(ATrain_AEval, S2),
        dependencies=(S2.inputs.x << ATrain_AEval.out_collections.z.a,),
    )
    assert set(ATrain_AEval_S2.outputs) == set()
    assert set(ATrain_AEval_S2.out_collections) == set(("z",))
    assert set(ATrain_AEval_S2.out_collections.z) == set(("b"))

    ATrain_duplicated = CombinedPipeline(
        name="ATrain_duplicated",
        pipelines=(ATrain,),
        outputs={
            "z.a": ATrain.outputs.z,
            "z.b": ATrain.outputs.z,
        },
    )
    assert set(ATrain_duplicated.outputs) == set()
    assert set(ATrain_duplicated.out_collections) == set(("z",))
    assert set(ATrain_duplicated.out_collections.z) == set(("a", "b"))
    dependencies = (ATrain_duplicated.out_collections.z.a >> S2.inputs.x,)
    ATrain_duplicated_S2 = CombinedPipeline(
        name="ATrain_duplicated_S2",
        pipelines=(ATrain_duplicated, S2),
        dependencies=dependencies,
    )
    assert set(ATrain_duplicated_S2.outputs) == set()
    # should be:
    # assert set(ATrain_duplicated_S2.out_collections) == set(("z",))
    # assert set(ATrain_duplicated_S2.out_collections.z) == set(("b",))
    # but instead we have:
    assert set(ATrain_duplicated_S2.out_collections) == set()
