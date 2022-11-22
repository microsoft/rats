"""These tests are copies of the examples in the docstrings of PipelineBuilder methods."""

from typing import Dict, TypedDict, TypeVar

import pytest

from oneml.processors import (
    Dependency,
    IProcess,
    OutProcessorParam,
    Pipeline,
    PipelineBuilder,
    frozendict,
)

Array = TypeVar("Array")

StandardizeOutput = TypedDict("StandardizeOutput", {"Z": float, "shift": float, "scale": float})


class Standardize(IProcess):
    def __init__(self, shift: float, scale: float) -> None:
        self._shift = shift
        self._scale = scale

    def process(self, X: float) -> StandardizeOutput:
        Z = (X - self._shift) / self._scale
        return StandardizeOutput({"Z": Z, "shift": self._shift, "scale": self._scale})


def test_predefined_standardize() -> None:
    predefined_standardize = PipelineBuilder.task(
        name="standardize",
        processor_type=Standardize,
        params_getter=frozendict(shift=10.0, scale=2.0),
    )

    assert set(predefined_standardize.inputs) == set(("X",))
    assert set(predefined_standardize.outputs) == set(("Z", "scale", "shift"))


def test_eval_standardize() -> None:
    eval_standardize = PipelineBuilder.task(name="standardize", processor_type=Standardize)

    assert set(eval_standardize.inputs) == set(("shift", "scale", "X"))
    assert set(eval_standardize.outputs) == set(("Z", "shift", "scale"))


def test_single_pipelineparams_assignments() -> None:
    train_standardize = PipelineBuilder.task(
        name="train",
        processor_type=Standardize,
        params_getter=frozendict(shift=10.0, scale=2.0),
    )
    eval_standardize = PipelineBuilder.task(name="eval", processor_type=Standardize)

    # Tests InCollection << OutCollection assignments
    dp = eval_standardize.inputs.shift << train_standardize.outputs.shift
    assert len(dp) == 1 and isinstance(dp[0], Dependency)

    with pytest.raises(TypeError):
        eval_standardize.inputs.shift >> train_standardize.outputs.shift  # type: ignore

    # Tests InParameter << OutParameter assignament
    dp = eval_standardize.inputs.shift.eval << train_standardize.outputs.shift.train
    assert len(dp) == 1 and isinstance(dp[0], Dependency)

    with pytest.raises(TypeError):
        eval_standardize.inputs.shift.eval >> train_standardize.outputs.shift.train  # type: ignore

    # Tests OutCollection >> InCollection assignments
    dp = train_standardize.outputs.scale >> eval_standardize.inputs.scale
    assert len(dp) == 1 and isinstance(dp[0], Dependency)

    with pytest.raises(TypeError):
        train_standardize.outputs.scale << eval_standardize.inputs.scale  # type: ignore

    # Tests OutParameter >> InParameter assignments
    dp = train_standardize.outputs.scale.train >> eval_standardize.inputs.scale.eval
    assert len(dp) == 1 and isinstance(dp[0], Dependency)

    with pytest.raises(TypeError):
        train_standardize.outputs.scale.train << eval_standardize.inputs.scale.eval  # type: ignore


def test_mixed_pipelineparams_assignments() -> None:
    train_standardize = PipelineBuilder.task(
        name="train",
        processor_type=Standardize,
        params_getter=frozendict(shift=10.0, scale=2.0),
    )
    eval_standardize = PipelineBuilder.task(name="eval", processor_type=Standardize)

    with pytest.raises(ValueError):  # not supported
        eval_standardize.inputs.shift.eval << train_standardize.outputs.shift  # type: ignore

    with pytest.raises(ValueError):  # not supported
        train_standardize.outputs.shift >> eval_standardize.inputs.shift.eval  # type: ignore

    with pytest.raises(ValueError):  # not supported
        eval_standardize.inputs.shift << train_standardize.outputs.shift.train  # type: ignore

    with pytest.raises(ValueError):  # not supported
        train_standardize.outputs.shift.train >> eval_standardize.inputs.shift  # type: ignore


def test_collection_pipelineparams_assignments() -> None:
    train_standardize = PipelineBuilder.task(
        name="train",
        processor_type=Standardize,
        params_getter=frozendict(shift=10.0, scale=2.0),
    )
    eval_standardize = PipelineBuilder.task(name="eval", processor_type=Standardize)
    stz1 = PipelineBuilder.combine(
        train_standardize,
        eval_standardize,
        dependencies=(
            train_standardize.outputs.shift >> eval_standardize.inputs.shift,
            train_standardize.outputs.scale >> eval_standardize.inputs.scale,
        ),
        name="stz1",
    )
    stz2 = PipelineBuilder.combine(
        train_standardize,
        eval_standardize,
        dependencies=(
            train_standardize.outputs.shift >> eval_standardize.inputs.shift,
            train_standardize.outputs.scale >> eval_standardize.inputs.scale,
        ),
        name="stz2",
    )

    # Tests InCollection << OutCollection assignments
    dps = stz2.inputs.X << stz1.outputs.Z  # many to many
    assert len(dps) == 2 and all(isinstance(dp, Dependency) for dp in dps)

    dps = stz2.inputs.X << stz1.outputs.shift  # one to many
    assert len(dps) == 2 and all(isinstance(dp, Dependency) for dp in dps)

    with pytest.raises(TypeError):
        stz2.inputs.X >> stz1.outputs.Z  # type: ignore

    # Tests InParameter << OutParameter assignments
    dp1 = stz2.inputs.X.train << stz1.outputs.Z.train
    dp2 = stz2.inputs.X.eval << stz1.outputs.Z.eval
    assert len(dp1) == 1 and isinstance(dp1[0], Dependency)
    assert len(dp2) == 1 and isinstance(dp2[0], Dependency)

    with pytest.raises(TypeError):
        stz2.inputs.X.train >> stz1.outputs.Z.train  # type: ignore
        stz2.inputs.X.eval >> stz1.outputs.Z.eval  # type: ignore

    # Tests OutCollection >> InCollection assignments
    dps = stz1.outputs.Z >> stz2.inputs.X  # many to many
    assert len(dps) == 2 and all(isinstance(dp, Dependency) for dp in dps)

    dps = stz1.outputs.shift >> stz2.inputs.X  # one to many
    assert len(dps) == 2 and all(isinstance(dp, Dependency) for dp in dps)

    with pytest.raises(TypeError):
        stz1.outputs.Z << stz2.inputs.X  # type: ignore

    # Tests OutParameter >> InParameter assignments
    dp1 = stz1.outputs.Z.train >> stz2.inputs.X.train
    dp2 = stz1.outputs.Z.eval >> stz2.inputs.X.eval
    assert len(dp1) == 1 and isinstance(dp1[0], Dependency)
    assert len(dp2) == 1 and isinstance(dp2[0], Dependency)

    with pytest.raises(TypeError):
        stz1.outputs.Z.train << stz1.inputs.X.train  # type: ignore
        stz1.outputs.Z.eval << stz1.inputs.X.eval  # type: ignore


class Scatter:
    def __init__(self, K: int) -> None:
        self._K = K

    @classmethod
    def get_return_annotation(cls, K: int) -> Dict[str, OutProcessorParam]:
        out_names = [f"in1_n{k}" for k in range(K)] + [f"in2_n{k}" for k in range(K)]
        return {out_name: OutProcessorParam(out_name, str) for out_name in out_names}

    def process(self, in1: str, in2: str) -> Dict[str, str]:
        return {f"in1_n{k}": f"{in1}_n{k}" for k in range(self._K)} | {
            f"in2_n{k}": f"{in2}_n{k}" for k in range(self._K)
        }


def test_scatter() -> None:
    scatter = PipelineBuilder.task(
        name="scatter",
        processor_type=Scatter,
        params_getter=frozendict(K=3),
        return_annotation=Scatter.get_return_annotation(3),
    )

    assert set(scatter.inputs) == set(("in1", "in2"))
    assert set(scatter.outputs) == set(
        ("in1_n0", "in1_n1", "in1_n2", "in2_n0", "in2_n1", "in2_n2")
    )


@pytest.fixture
def w1() -> Pipeline:
    W1Output = TypedDict("W1Output", {"C": str})

    class W1:
        def process(self, A: str, B: str) -> W1Output:
            ...

    return PipelineBuilder.task(W1, "w1")


@pytest.fixture
def w2() -> Pipeline:
    W2Output = TypedDict("W2Output", {"E": str, "F": str})

    class W2:
        def process(self, D: str) -> W2Output:
            ...

    return PipelineBuilder.task(W2, "w2")


@pytest.fixture
def w3() -> Pipeline:
    W3Output = TypedDict("W3Output", {"H": str})

    class W3:
        def process(self, A: str, G: str) -> W3Output:
            ...

    return PipelineBuilder.task(W3, "w3")


@pytest.fixture
def w4() -> Pipeline:
    W4Output = TypedDict("W4Output", {"E": str})

    class W4:
        def process(self, A: str) -> W4Output:
            ...

    return PipelineBuilder.task(W4, "w4")


def test_no_dependencies_default_inputs_and_outputs(w1: Pipeline, w2: Pipeline) -> None:
    combined = PipelineBuilder.combine(w1, w2, name="combined")

    assert set(combined.inputs) == set(("A", "B", "D"))
    assert set(combined.outputs) == set(("C", "E", "F"))


def test_with_dependencies_default_inputs_and_outputs(
    w1: Pipeline, w2: Pipeline, w3: Pipeline
) -> None:
    combined = PipelineBuilder.combine(
        w1,
        w2,
        w3,
        name="combined",
        dependencies=(
            w1.outputs.C >> w2.inputs.D,
            w1.outputs.C >> w3.inputs.A,
            w2.outputs.E >> w3.inputs.G,
        ),
    )

    assert set(combined.inputs) == set(("A", "B"))
    assert set(combined.outputs) == set(("F", "H"))


def test_with_dependencies_default_inputs_and_outputs_with_shared_input(
    w1: Pipeline, w2: Pipeline, w3: Pipeline
) -> None:
    combined = PipelineBuilder.combine(
        w1,
        w2,
        w3,
        name="combined",
        dependencies=(
            w1.outputs.C >> w2.inputs.D,
            w2.outputs.E >> w3.inputs.G,
        ),
    )

    assert set(combined.inputs) == set(("A", "B"))
    assert set(combined.outputs) == set(("F", "H"))


def test_with_dependencies_inputs_and_outputs_specified(
    w1: Pipeline, w2: Pipeline, w3: Pipeline, w4: Pipeline
) -> None:
    combined = PipelineBuilder.combine(
        w1,
        w2,
        w3,
        w4,
        name="combined",
        dependencies=(
            w1.outputs.C >> w2.inputs.D,
            w1.outputs.C >> w3.inputs.A,
            w2.outputs.E >> w3.inputs.G,
            w2.outputs.E >> w4.inputs.A,
        ),
        inputs={
            "a1": w1.inputs.A,
            "b": w1.inputs.B,
            "a2": w3.inputs.A,
        },
        outputs={"c": w1.outputs.C, "h": w3.outputs.H, "e": w4.outputs.E},
    )

    assert set(combined.inputs) == set(("a1", "b", "a2"))
    assert set(combined.outputs) == set(("c", "h", "e"))


def test_missing_input_error(w1: Pipeline, w2: Pipeline) -> None:
    with pytest.raises(ValueError):
        _ = PipelineBuilder.combine(
            w1,
            w2,
            name="combined",
            dependencies=(w1.outputs.C >> w2.inputs.D,),
            inputs={"a": w1.inputs.A},
        )

    mitigated_combined = PipelineBuilder.combine(
        w1,
        w2,
        name="combined",
        dependencies=(w1.outputs.C >> w2.inputs.D,),
        inputs={
            "a": w1.inputs.A,
            "b": w1.inputs.B,
        },
    )

    assert set(mitigated_combined.inputs) == set(("a", "b"))
    assert set(mitigated_combined.outputs) == set(("E", "F"))


def test_clashing_outputs_error(w2: Pipeline, w4: Pipeline) -> None:
    combined = PipelineBuilder.combine(w2, w4, name="combined")
    assert set(combined.inputs) == set(("D", "A"))
    assert set(combined.outputs) == set(("F", "E"))
    assert set(combined.outputs.F) == set(("w2",))
    assert set(combined.outputs.E) == set(("w2", "w4"))

    mitigated_combined = PipelineBuilder.combine(
        w2, w4, name="combined", outputs={"e": w2.outputs.E}
    )
    assert set(mitigated_combined.inputs) == set(("D", "A"))
    assert set(mitigated_combined.outputs) == set(("e"))
