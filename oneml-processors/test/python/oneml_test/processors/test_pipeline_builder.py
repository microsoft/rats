"""These tests are copies of the examples in the docstrings of PipelineBuilder methods."""

from abc import abstractmethod
from typing import Dict, TypedDict, TypeVar

import pytest

from oneml.processors import IProcess, Pipeline, PipelineBuilder, frozendict

Array = TypeVar("Array")

StandardizeOutput = TypedDict("StandardizeOutput", {"Z": float, "shift": int, "scale": int})


class Standardize(IProcess):
    def __init__(self, shift: int, scale: int) -> None:
        self._shift = shift
        self._scale = scale

    def process(self, X: float) -> StandardizeOutput:
        Z = (X - self._shift) / self._scale
        return StandardizeOutput({"Z": Z, "shift": self._shift, "scale": self._scale})


class Scatter:
    def __init__(self, K: int) -> None:
        self._K = K

    @classmethod
    def get_return_annotation(cls, K: int) -> Dict[str, type]:
        out_names = [f"in1_n{k}" for k in range(K)] + [f"in2_n{k}" for k in range(K)]
        return {out_name: str for out_name in out_names}

    def process(self, in1: str, in2: str) -> Dict[str, str]:
        return {f"in1_n{k}": f"{in1}_n{k}" for k in range(self._K)} | {
            f"in2_n{k}": f"{in2}_n{k}" for k in range(self._K)
        }


@pytest.fixture
def train_stz() -> Pipeline:
    return PipelineBuilder.task(Standardize, params_getter=frozendict(shift=10.0, scale=2.0))


@pytest.fixture
def eval_stz() -> Pipeline:
    return PipelineBuilder.task(Standardize)


@pytest.fixture
def scatter() -> Pipeline:
    return PipelineBuilder.task(
        processor_type=Scatter,
        name="scatter",
        params_getter=frozendict(K=3),
        return_annotation=Scatter.get_return_annotation(3),
    )


def test_predefined_standardize(train_stz: Pipeline) -> None:
    assert set(train_stz.inputs) == set(("X",))
    assert set(train_stz.outputs) == set(("Z", "scale", "shift"))


def test_eval_stz(eval_stz: Pipeline) -> None:
    assert set(eval_stz.inputs) == set(("shift", "scale", "X"))
    assert set(eval_stz.outputs) == set(("Z", "shift", "scale"))


def test_scatter(scatter: Pipeline) -> None:
    assert set(scatter.inputs) == set(("in1", "in2"))
    assert set(scatter.outputs) == set(
        ("in1_n0", "in1_n1", "in1_n2", "in2_n0", "in2_n1", "in2_n2")
    )


@pytest.fixture
def w1() -> Pipeline:
    W1Output = TypedDict("W1Output", {"C": str})

    class W1:
        @abstractmethod
        def process(self, A: str, B: str) -> W1Output:
            ...

    return PipelineBuilder.task(W1, name="w1")


@pytest.fixture
def w2() -> Pipeline:
    W2Output = TypedDict("W2Output", {"E": str, "F": str})

    class W2:
        @abstractmethod
        def process(self, D: str) -> W2Output:
            ...

    return PipelineBuilder.task(W2, name="w2")


@pytest.fixture
def w3() -> Pipeline:
    W3Output = TypedDict("W3Output", {"H": str})

    class W3:
        @abstractmethod
        def process(self, A: str, G: str) -> W3Output:
            ...

    return PipelineBuilder.task(W3, name="w3")


@pytest.fixture
def w4() -> Pipeline:
    W4Output = TypedDict("W4Output", {"E": str})

    class W4:
        @abstractmethod
        def process(self, A: str) -> W4Output:
            ...

    return PipelineBuilder.task(W4, name="w4")


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
        },
        outputs={"c": w1.outputs.C, "h": w3.outputs.H, "e": w4.outputs.E},
    )

    assert set(combined.inputs) == set(("a1", "b"))
    assert set(combined.outputs) == set(("c", "h", "e"))

    with pytest.raises(ValueError):
        PipelineBuilder.combine(
            w1,
            w3,
            name="combined",
            dependencies=(w1.outputs.C >> w3.inputs.A,),
            inputs={"a2": w3.inputs.A},  # inputs are specified also as dependencies
            outputs={},
        )


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
    assert set(combined.outputs.F) == set(w2.decorate("combined").outputs.F)
    assert len(combined.outputs.E) == 1

    mitigated_combined = PipelineBuilder.combine(
        w2, w4, name="combined", outputs={"e": w2.outputs.E}
    )
    assert set(mitigated_combined.inputs) == set(("D", "A"))
    assert set(mitigated_combined.outputs) == set(("e"))
