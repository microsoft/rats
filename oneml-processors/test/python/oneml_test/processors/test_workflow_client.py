"""These tests are copies of the examples in the docstrings of WorkflowClient methods."""

from typing import Dict, TypedDict, TypeVar

import pytest

from oneml.processors import IProcess, OutParameter, WorkflowClient, frozendict

Array = TypeVar("Array")

StandardizeOutput = TypedDict("StandardizeOutput", {"Z": Array})


class Standardize(IProcess):
    def __init__(self, shift: float, scale: float) -> None:
        self._shift = shift
        self._scale = scale

    def process(self, X: Array) -> StandardizeOutput:
        Z = (X - self._shift) / self._scale
        return StandardizeOutput({"Z": Z})


def test_predefined_standardize():
    predefined_standardize = WorkflowClient.single_task(
        name="standardize",
        processor_type=Standardize,
        params_getter=frozendict(
            shift=10.0,
            scale=2.0,
        ),
    )

    assert set(predefined_standardize.sig) == set(("X",))
    assert set(predefined_standardize.ret) == set(("Z",))


def test_eval_standardize():
    eval_standardize = WorkflowClient.single_task(
        name="standardize", processor_type=Standardize, params_getter=frozendict()
    )

    assert set(eval_standardize.sig) == set(
        (
            "shift",
            "scale",
            "X",
        )
    )
    assert set(eval_standardize.ret) == set(("Z",))


class Scatter:
    def __init__(self, K: int) -> None:
        self._K = K

    @classmethod
    def get_return_annotation(cls, K: int) -> Dict[str, OutParameter]:
        out_names = [f"in1_{k}" for k in range(K)] + [f"in2_{k}" for k in range(K)]
        return {out_name: OutParameter(out_name, str) for out_name in out_names}

    def process(self, in1: str, in2: str) -> Dict[str, str]:
        return {f"in1_{k}": f"{in1}_{k}" for k in range(self._K)} | {
            f"in2_{k}": f"{in2}_{k}" for k in range(self._K)
        }


def test_scatter():
    scatter = WorkflowClient.single_task(
        name="scatter",
        processor_type=Scatter,
        params_getter=frozendict(K=3),
        return_annotation=Scatter.get_return_annotation(3),
    )

    assert set(scatter.sig) == set(("in1", "in2"))
    assert set(scatter.ret) == set(("in1_0", "in1_1", "in1_2", "in2_0", "in2_1", "in2_2"))


@pytest.fixture
def w1():
    W1Output = TypedDict("W1Output", {"C": str})

    class W1:
        def process(self, A: str, B: str) -> W1Output:
            ...

    return WorkflowClient.single_task("w1", W1)


@pytest.fixture
def w2():
    W2Output = TypedDict("W2Output", {"E": str, "F": str})

    class W2:
        def process(self, D: str) -> W2Output:
            ...

    return WorkflowClient.single_task("w2", W2)


@pytest.fixture
def w3():
    W3Output = TypedDict("W3Output", {"H": str})

    class W3:
        def process(self, A: str, G: str) -> W3Output:
            ...

    return WorkflowClient.single_task("w3", W3)


@pytest.fixture
def w4():
    W4Output = TypedDict("W4Output", {"E": str})

    class W4:
        def process(self, A: str) -> W4Output:
            ...

    return WorkflowClient.single_task("w4", W4)


def test_no_dependencies_default_inputs_and_outputs(w1, w2):
    combined = WorkflowClient.compose_workflow(name="combined", workflows=(w1, w2))

    assert set(combined.sig) == set(("A", "B", "D"))
    assert set(combined.ret) == set(("C", "E", "F"))


def test_with_dependencies_default_inputs_and_outputs(w1, w2, w3):
    combined = WorkflowClient.compose_workflow(
        name="combined",
        workflows=(w1, w2, w3),
        dependencies=(
            w1.ret.C >> w2.sig.D,
            w1.ret.C >> w3.sig.A,
            w2.ret.E >> w3.sig.G,
        ),
    )

    assert set(combined.sig) == set(("A", "B"))
    assert set(combined.ret) == set(("F", "H"))


def test_with_dependencies_default_inputs_and_outputs_with_shared_input(w1, w2, w3):
    combined = WorkflowClient.compose_workflow(
        name="combined",
        workflows=(w1, w2, w3),
        dependencies=(
            w1.ret.C >> w2.sig.D,
            w2.ret.E >> w3.sig.G,
        ),
    )

    assert set(combined.sig) == set(("A", "B"))
    assert set(combined.ret) == set(("F", "H"))


def test_with_dependencies_inputs_and_outputs_specified(w1, w2, w3, w4):
    combined = WorkflowClient.compose_workflow(
        name="combined",
        workflows=(w1, w2, w3, w4),
        dependencies=(
            w1.ret.C >> w2.sig.D,
            w1.ret.C >> w3.sig.A,
            w2.ret.E >> w3.sig.G,
            w2.ret.E >> w4.sig.A,
        ),
        input_dependencies=(
            "a1" >> w1.sig.A,
            "b" >> w1.sig.B,
            "a2" >> w3.sig.A,
        ),
        output_dependencies=(
            w1.ret.C >> "c",
            w3.ret.H >> "h",
            w4.ret.E >> "e",
        ),
    )

    assert set(combined.sig) == set(("a1", "b", "a2"))
    assert set(combined.ret) == set(("c", "h", "e"))


def test_missing_input_error(w1, w2):
    with pytest.raises(ValueError):
        _ = WorkflowClient.compose_workflow(
            name="combined",
            workflows=(w1, w2),
            dependencies=(w1.ret.C >> w2.sig.D,),
            input_dependencies=("a" >> w1.sig.A,),
        )

    mitigated_combined = WorkflowClient.compose_workflow(
        name="combined",
        workflows=(w1, w2),
        dependencies=(w1.ret.C >> w2.sig.D,),
        input_dependencies=(
            "a" >> w1.sig.A,
            "b" >> w1.sig.B,
        ),
    )

    assert set(mitigated_combined.sig) == set(("a", "b"))
    assert set(mitigated_combined.ret) == set(("E", "F"))


def test_clashing_outputs_error(w2, w4):
    with pytest.raises(ValueError):
        _ = WorkflowClient.compose_workflow(
            name="combined",
            workflows=(w2, w4),
        )

    mitigated_combined = WorkflowClient.compose_workflow(
        name="combined", workflows=(w2, w4), output_dependencies=(w2.ret.E >> "e",)
    )

    assert set(mitigated_combined.sig) == set(("D", "A"))
    assert set(mitigated_combined.ret) == set(("e"))
