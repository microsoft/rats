from typing import Any, Dict, FrozenSet, Mapping, Sequence, TypedDict

import numpy as np
import numpy.typing as npt
import pytest

from oneml.processors import (
    DataArg,
    FrozenDict,
    Namespace,
    PDependency,
    Pipeline,
    PipelineSessionProvider,
    PNode,
    PNodeProperties,
    Processor,
    Provider,
)

ArrayReaderOutput = TypedDict("ArrayReaderOutput", {"array": npt.ArrayLike})
ArrayDotProductOutput = TypedDict("ArrayDotProductOutput", {"output": npt.ArrayLike})
ArrayConcatenatorOutput = TypedDict("ArrayConcatenatorOutput", {"output": npt.ArrayLike})
TDict = Mapping[str, Any]


class ArrayReader(Processor[ArrayReaderOutput]):
    def __init__(self, storage: Mapping[str, npt.NDArray[np.float64]], url: str) -> None:
        super().__init__()
        self._storage = storage
        self._url = url

    def process(self) -> ArrayReaderOutput:
        return ArrayReaderOutput(array=self._storage[self._url])


class ArrayDotProduct(Processor[ArrayDotProductOutput]):
    def process(
        self, left: npt.ArrayLike = np.zeros(1), right: npt.ArrayLike = np.zeros(1)
    ) -> ArrayDotProductOutput:
        return ArrayDotProductOutput(output=np.dot(left, right))


class ArrayConcat(Processor[ArrayConcatenatorOutput]):
    def __init__(self, num_inputs: int) -> None:
        super().__init__()
        self._num_inputs = num_inputs

    def process(self, arrays: Sequence[npt.ArrayLike] = ()) -> ArrayConcatenatorOutput:
        concatenated = np.concatenate([np.reshape(a, newshape=(-1,)) for a in arrays])
        return ArrayConcatenatorOutput(output=concatenated)


@pytest.fixture
def storage() -> Dict[str, npt.NDArray[np.float64]]:
    return {"a": np.array([10.0, 20.0, 30.0]), "b": np.array([-10.0, 20.0, -30.0])}


@pytest.fixture
def simple_pipeline(storage: Mapping[str, npt.NDArray[np.float64]]) -> Pipeline:
    left_arr = PNode("left_arr")
    right_arr = PNode("right_arr")
    multiply = PNode("multiply")
    nodes = frozenset((left_arr, right_arr, multiply))
    dependencies: FrozenDict[
        PNode, FrozenSet[PDependency[npt.ArrayLike, npt.ArrayLike]]
    ] = FrozenDict(
        {
            multiply: frozenset(
                (
                    PDependency(
                        left_arr,
                        in_arg=DataArg[npt.ArrayLike]("left"),
                        out_arg=DataArg[npt.NDArray[np.float64]]("array"),
                    ),
                    PDependency(
                        right_arr,
                        in_arg=DataArg[npt.ArrayLike]("right"),
                        out_arg=DataArg[npt.NDArray[np.float64]]("array"),
                    ),
                )
            )
        }
    )
    props: FrozenDict[PNode, PNodeProperties[TDict]] = FrozenDict(
        {
            left_arr: PNodeProperties(Provider(ArrayReader, {"storage": storage, "url": "a"})),
            right_arr: PNodeProperties(Provider(ArrayReader, {"storage": storage, "url": "b"})),
            multiply: PNodeProperties(Provider(ArrayDotProduct)),
        }
    )
    pipeline = Pipeline(nodes, dependencies, props)
    return pipeline


@pytest.fixture
def complex_pipeline(simple_pipeline: Pipeline) -> Pipeline:
    p1 = simple_pipeline.decorate(Namespace("p1"))
    p2 = simple_pipeline.decorate(Namespace("p2"))
    p3 = simple_pipeline.decorate(Namespace("p3"))
    concat_node = PNode("ArrayConcat")
    concat_nodes = frozenset((concat_node,))
    concat_dps: FrozenDict[
        PNode, FrozenSet[PDependency[npt.ArrayLike, npt.ArrayLike]]
    ] = FrozenDict(
        {
            concat_node: frozenset(
                (
                    PDependency(p1, in_arg=("arrays", npt.ArrayLike)),  # type: ignore[arg-type]
                    PDependency(p2, in_arg=("arrays", npt.ArrayLike)),  # type: ignore[arg-type]
                    PDependency(p3, in_arg=("arrays", npt.ArrayLike)),  # type: ignore[arg-type]
                )
            )
        }
    )
    concat_props: FrozenDict[PNode, PNodeProperties[TDict]] = FrozenDict(
        {concat_node: PNodeProperties(Provider(ArrayConcat, {"num_inputs": 3}))}
    )
    concat_pipeline = Pipeline(concat_nodes, concat_dps, concat_props)
    return p1 + p2 + p3 + concat_pipeline


def test_simple_pipeline(simple_pipeline: Pipeline) -> None:
    session = PipelineSessionProvider.get_session(simple_pipeline)
    session.run()
