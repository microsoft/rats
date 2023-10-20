from abc import abstractmethod
from dataclasses import dataclass
from typing import TypedDict, cast

import pytest

from oneml.processors.dag import IProcess
from oneml.processors.ux import CombinedPipeline, UPipeline, UTask


@dataclass
class Array:
    ...


class ReportGenerator(IProcess):
    @abstractmethod
    def process(self, acc: Array) -> None:
        ...


@pytest.fixture
def report1() -> UPipeline:
    return cast(UPipeline, UTask(ReportGenerator, "report1").rename_inputs({"acc": "acc.report1"}))


@pytest.fixture
def report2() -> UPipeline:
    return cast(UPipeline, UTask(ReportGenerator, "report2").rename_inputs({"acc": "acc.report2"}))


def test_sequence_inputs_to_single_output(report1: UPipeline, report2: UPipeline) -> None:
    # Inputs <- Inputs | Inputs
    reportsA: UPipeline = CombinedPipeline(
        pipelines=[report1, report2],
        name="reportsA",
        inputs={"acc": report1.inputs.acc | report2.inputs.acc},
    )
    assert len(reportsA.inputs) == 1
    assert len(reportsA.inputs.acc) == 2
    assert reportsA.inputs.acc.report1 == report1.decorate("reportsA").inputs.acc.report1
    assert reportsA.inputs.acc.report2 == report2.decorate("reportsA").inputs.acc.report2

    # Inputs <- InPort
    reportsB: UPipeline = CombinedPipeline(
        pipelines=[report1, report2],
        name="reportsB",
        inputs={
            "acc.report1": report1.inputs.acc.report1,
            "acc.report2": report2.inputs.acc.report2,
        },
    )
    assert len(reportsB.inputs) == 1
    assert len(reportsB.inputs.acc) == 2
    assert reportsB.inputs.acc.report1 == report1.decorate("reportsB").inputs.acc.report1
    assert reportsB.inputs.acc.report2 == report2.decorate("reportsB").inputs.acc.report2

    # Inputs | InPort -> raises TypeError
    with pytest.raises(TypeError):
        report1.inputs.acc | report2.inputs.acc.report2

    # Inputs.InPort <- InPort | InPort
    reportsC: UPipeline = CombinedPipeline(
        pipelines=[report1, report2],
        name="reportsC",
        inputs={"acc.r": report1.inputs.acc.report1 | report2.inputs.acc.report2},
    )
    assert len(reportsC.inputs) == 1
    assert len(reportsC.inputs.acc) == 1
    assert len(reportsC.inputs.acc.r) == 2
    assert (
        reportsC.inputs.acc.r
        == report1.decorate("reportsC").inputs.acc.report1
        | report2.decorate("reportsC").inputs.acc.report2
    )

    # Inputs.InPort <- Inputs | Inputs
    reportsC = CombinedPipeline(
        pipelines=[report1, report2],
        name="reportsC",
        inputs={"acc.r": report1.inputs.acc.report1 | report2.inputs.acc.report2},
    )
    assert len(reportsC.inputs) == 1
    assert len(reportsC.inputs.acc) == 1
    assert len(reportsC.inputs.acc.r) == 2
    assert (
        reportsC.inputs.acc.r
        == report1.decorate("reportsC").inputs.acc.report1
        | report2.decorate("reportsC").inputs.acc.report2
    )

    # InPort <- InPort | Inputs
    with pytest.raises(TypeError):
        report1.inputs.acc.report1 | report2.inputs.acc


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
def ATrain() -> UTask:
    return UTask(AProcessor, "train")


@pytest.fixture
def AEval() -> UTask:
    return UTask(AProcessor, "eval")


@pytest.fixture
def BTrain() -> UTask:
    return UTask(BProcessor, "train")


@pytest.fixture
def BEval() -> UTask:
    return UTask(BProcessor, "eval")


@pytest.fixture
def CTrain() -> UTask:
    return UTask(CProcessor, "train")


@pytest.fixture
def CEval() -> UTask:
    return UTask(CProcessor, "eval")


@pytest.fixture
def Sink() -> UTask:
    return UTask(SinkProcessor, "sync")


@pytest.fixture
def A(ATrain: UPipeline, AEval: UPipeline) -> UPipeline:
    return CombinedPipeline(pipelines=[ATrain, AEval], name="A")


@pytest.fixture
def B(BTrain: UPipeline) -> UPipeline:
    return CombinedPipeline(pipelines=[BTrain], name="B")


@pytest.fixture
def C(CTrain: UPipeline, CEval: UPipeline) -> UPipeline:
    return CombinedPipeline(pipelines=[CTrain, CEval], name="C")


@pytest.fixture
def ABC(A: UPipeline, B: UPipeline, C: UPipeline) -> UPipeline:
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


def test_combine_inputs(A: UPipeline, B: UPipeline, C: UPipeline, ABC: UPipeline) -> None:
    assert set(ABC.inputs) == set(("x",))
    assert ABC.inputs.x == A.inputs.x.decorate("ABC")
    assert set(ABC.outputs) == set(("z_A", "z_B", "z_C", "z"))
    assert ABC.outputs.z_A == A.outputs.z.decorate("ABC")
    assert ABC.outputs.z_B == B.outputs.z.decorate("ABC")
    assert ABC.outputs.z_C == C.outputs.z.decorate("ABC")
    assert set(ABC.outputs.z) == set(("A_eval", "B_train", "C_eval", "C_train"))
    assert ABC.outputs.z.A_eval == A.outputs.z.decorate("ABC")
    assert ABC.outputs.z.C_eval == C.outputs.z.decorate("ABC")
    assert ABC.outputs.z.B_train == B.outputs.z.decorate("ABC")
    assert ABC.outputs.z.C_train == C.outputs.z.decorate("ABC")

    # InPort <- InPort | InPort
    D1: UPipeline = CombinedPipeline(
        pipelines=[B, C], name="D1", inputs={"x": B.inputs.x | C.inputs.x}, outputs={}
    )
    assert D1.inputs.x == (B.inputs.x | C.inputs.x).decorate("D1")

    # Inputs.InPort <- InPort | InPort
    D2: UPipeline = CombinedPipeline(
        pipelines=[B, C],
        name="D2",
        inputs={
            "x.train": B.inputs.x | C.inputs.x,
            "x.eval": C.inputs.x,
        },
        outputs={},
    )
    assert D2.inputs.x.train == (B.inputs.x | C.inputs.x).decorate("D2")
    assert D2.inputs.x.eval == C.inputs.x.decorate("D2")

    # InPort <- Inputs | Inputs
    D3: UPipeline = CombinedPipeline(
        pipelines=[B, C],
        name="D3",
        inputs={
            "x": B.inputs.x | C.inputs.x,
        },
        outputs={},
    )
    assert D3.inputs.x == (B.inputs.x | C.inputs.x).decorate("D3")


def test_combine_outputs(ATrain: UPipeline, AEval: UPipeline, Sink: UPipeline) -> None:
    # This test shows a bug in the default mechanism for defining the outputs of CombinedPipeline.
    # The signatures of ATrain_AEval and of ATrain_duplicated are identical - both have a single
    # output collection - 'z', with two entries, 'a', and 'b'.
    # When combining ATrain_AEval with S2, using z.a in a dependency, we get the expected output
    # signature - z.b, because z.a was used and removed from the output signature.
    # But when combining ATrain_duplicated with S2, using z.a in a dependency, we get no output.
    S2: UPipeline = CombinedPipeline(
        name="S2",
        pipelines=(Sink.decorate("S1"), Sink.decorate("S2"), Sink.decorate("S3")),
    )
    ATrain_AEval: UPipeline = CombinedPipeline(
        name="ATrain_AEval",
        pipelines=(ATrain, AEval),
        outputs={
            "z.a": ATrain.outputs.z,
            "z.b": AEval.outputs.z,
        },
    )
    assert set(ATrain_AEval.outputs) == set(("z",))
    assert set(ATrain_AEval.outputs.z) == set(("a", "b"))
    ATrain_AEval_S2: UPipeline = CombinedPipeline(
        name="ATrain_AEval_S2",
        pipelines=(ATrain_AEval, S2),
        dependencies=(S2.inputs.x << ATrain_AEval.outputs.z.a,),
    )
    assert set(ATrain_AEval_S2.outputs) == set(("z",))
    assert set(ATrain_AEval_S2.outputs.z) == set(("b"))

    ATrain_duplicated: UPipeline = CombinedPipeline(
        name="ATrain_duplicated",
        pipelines=(ATrain,),
        outputs={
            "z.a": ATrain.outputs.z,
            "z.b": ATrain.outputs.z,
        },
    )
    assert set(ATrain_duplicated.outputs) == set(("z",))
    assert set(ATrain_duplicated.outputs.z) == set(("a", "b"))
    dependencies = (ATrain_duplicated.outputs.z.a >> S2.inputs.x,)
    ATrain_duplicated_S2: UPipeline = CombinedPipeline(
        name="ATrain_duplicated_S2",
        pipelines=(ATrain_duplicated, S2),
        dependencies=dependencies,
    )
    assert set(ATrain_duplicated_S2.outputs) == set()
    # should be:
    # assert set(ATrain_duplicated_S2.outputs) == set(("z",))
    # assert set(ATrain_duplicated_S2.outputs.z) == set(("b",))
    # but instead we have:
    assert set(ATrain_duplicated_S2.outputs) == set()
