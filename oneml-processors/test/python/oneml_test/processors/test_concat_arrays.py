from typing import Any, Mapping, TypedDict

import numpy as np
import numpy.typing as npt
import pytest

from oneml.processors import (
    InParameter,
    IProcessor,
    Namespace,
    OutParameter,
    PDependency,
    Pipeline,
    PipelineSessionProvider,
    PNode,
    PNodeProperties,
    Provider,
)

ArrayReaderOutput = TypedDict("ArrayReaderOutput", {"array": npt.NDArray[np.float64]})
ArrayDotProductOutput = TypedDict("ArrayDotProductOutput", {"output": npt.NDArray[np.float64]})
ArrayConcatenatorOutput = TypedDict("ArrayConcatenatorOutput", {"output": npt.NDArray[np.float64]})
TDict = Mapping[str, Any]


class ArrayReader(IProcessor):
    def __init__(self, storage: Mapping[str, npt.NDArray[np.float64]], url: str) -> None:
        super().__init__()
        self._storage = storage
        self._url = url

    def process(self) -> ArrayReaderOutput:
        return ArrayReaderOutput(array=self._storage[self._url])


class ArrayDotProduct(IProcessor):
    def process(
        self, left: npt.NDArray[np.float64], right: npt.NDArray[np.float64]
    ) -> ArrayDotProductOutput:
        return ArrayDotProductOutput(output=np.dot(left, right))


class ArrayConcat(IProcessor):
    def __init__(self, num_inputs: int) -> None:
        super().__init__()
        self._num_inputs = num_inputs

    def process(self, *arrays: npt.NDArray[np.float64]) -> ArrayConcatenatorOutput:
        concatenated = np.concatenate([np.reshape(a, newshape=(-1,)) for a in arrays])
        return ArrayConcatenatorOutput(output=concatenated)


@pytest.fixture
def storage() -> dict[str, npt.NDArray[np.float64]]:
    return {"a": np.array([10.0, 20.0, 30.0]), "b": np.array([-10.0, 20.0, -30.0])}


@pytest.fixture
def simple_pipeline(storage: Mapping[str, npt.NDArray[np.float64]]) -> Pipeline:
    left_arr = PNode("left_arr")
    right_arr = PNode("right_arr")
    multiply = PNode("multiply")
    nodes = set((left_arr, right_arr, multiply))
    dependencies: dict[PNode, set[PDependency]] = {
        multiply: set(
            (
                PDependency(
                    left_arr,
                    in_arg=InParameter("left", npt.NDArray[np.float64]),
                    out_arg=OutParameter("array", npt.NDArray[np.float64]),
                ),
                PDependency(
                    right_arr,
                    in_arg=InParameter("right", npt.NDArray[np.float64]),
                    out_arg=OutParameter("array", npt.NDArray[np.float64]),
                ),
            )
        )
    }

    props: dict[PNode, PNodeProperties] = {
        left_arr: PNodeProperties(Provider(ArrayReader, {"storage": storage, "url": "a"})),
        right_arr: PNodeProperties(Provider(ArrayReader, {"storage": storage, "url": "b"})),
        multiply: PNodeProperties(Provider(ArrayDotProduct)),
    }
    pipeline = Pipeline(nodes, dependencies, props)
    return pipeline


@pytest.fixture
def complex_pipeline(simple_pipeline: Pipeline) -> Pipeline:
    p1 = simple_pipeline.decorate(Namespace("p1"))
    p2 = simple_pipeline.decorate(Namespace("p2"))
    p3 = simple_pipeline.decorate(Namespace("p3"))
    concat_node = PNode("array_concat")
    concat_nodes = set((concat_node,))
    concat_dps: dict[PNode, set[PDependency]] = {
        concat_node: set(
            (
                PDependency(
                    p1,
                    in_arg=InParameter(
                        "arrays", npt.NDArray[np.float64], InParameter.VAR_POSITIONAL
                    ),
                    out_arg=OutParameter("output", npt.NDArray[np.float64]),
                ),
                PDependency(
                    p2,
                    in_arg=InParameter(
                        "arrays", npt.NDArray[np.float64], InParameter.VAR_POSITIONAL
                    ),
                    out_arg=OutParameter("output", npt.NDArray[np.float64]),
                ),
                PDependency(
                    p3,
                    in_arg=InParameter(
                        "arrays", npt.NDArray[np.float64], InParameter.VAR_POSITIONAL
                    ),
                    out_arg=OutParameter("output", npt.NDArray[np.float64]),
                ),
            )
        )
    }

    concat_props: dict[PNode, PNodeProperties] = {
        concat_node: PNodeProperties(Provider(ArrayConcat, {"num_inputs": 3}))
    }

    concat_pipeline = Pipeline(concat_nodes, concat_dps, concat_props)
    return p1 + p2 + p3 + concat_pipeline


def test_simple_pipeline(simple_pipeline: Pipeline) -> None:
    session = PipelineSessionProvider.get_session(simple_pipeline)
    session.run()


def test_complex_pipeline(complex_pipeline: Pipeline) -> None:
    session = PipelineSessionProvider.get_session(complex_pipeline)
    session.run()
