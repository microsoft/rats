from typing import Mapping, TypedDict

import numpy as np
import numpy.typing as npt
import pytest

from oneml.processors import (
    IProcess,
    IRegistryOfSingletonFactories,
    KnownParamsGetter,
    Namespace,
    PDependency,
    Pipeline,
    PipelineSessionProvider,
    PNode,
    frozendict,
)
from oneml.processors._pipeline import InParameter, OutParameter, ProcessorProps

ArrayReaderOutput = TypedDict("ArrayReaderOutput", {"array": npt.NDArray[np.float64]})
ArrayDotProductOutput = TypedDict("ArrayDotProductOutput", {"output": npt.NDArray[np.float64]})
SumArraysOutput = TypedDict("SumArraysOutput", {"output": npt.NDArray[np.float64]})


class ArrayReader(IProcess):
    def __init__(self, storage: Mapping[str, npt.NDArray[np.float64]], url: str) -> None:
        super().__init__()
        self._storage = storage
        self._url = url

    def process(self) -> ArrayReaderOutput:
        return ArrayReaderOutput(array=self._storage[self._url])


class ArrayDotProduct(IProcess):
    def process(
        self, left: npt.NDArray[np.float64], right: npt.NDArray[np.float64]
    ) -> ArrayDotProductOutput:
        return ArrayDotProductOutput(output=np.dot(left, right))


class SumArrays(IProcess):
    def process(self, *arrays: npt.NDArray[np.float64]) -> SumArraysOutput:
        return SumArraysOutput(output=np.sum([np.sum(a) for a in arrays]))


class ExampleConfig(KnownParamsGetter):
    def __init__(self, url: str) -> None:
        super().__init__(
            dict(
                url=url,
                storage={"a": np.array([10.0, 20.0, 30.0]), "b": np.array([-10.0, 20.0, -30.0])},
            )
        )


@pytest.fixture
def simple_pipeline() -> Pipeline:
    left_arr = PNode("left_arr")
    right_arr = PNode("right_arr")
    multiply = PNode("multiply")
    nodes = {
        left_arr: ProcessorProps(ArrayReader, ExampleConfig("a")),
        right_arr: ProcessorProps(ArrayReader, ExampleConfig("b")),
        multiply: ProcessorProps(ArrayDotProduct),
    }
    dependencies: dict[PNode, set[PDependency]] = {
        multiply: set(
            (
                PDependency(
                    left_arr,
                    in_arg=InParameter("left", npt.NDArray[np.float64], ArrayDotProduct.process),
                    out_arg=OutParameter("array", npt.NDArray[np.float64]),
                ),
                PDependency(
                    right_arr,
                    in_arg=InParameter("right", npt.NDArray[np.float64], ArrayDotProduct.process),
                    out_arg=OutParameter("array", npt.NDArray[np.float64]),
                ),
            )
        )
    }

    return Pipeline(nodes, dependencies)


@pytest.fixture
def complex_pipeline(simple_pipeline: Pipeline) -> Pipeline:
    p1 = simple_pipeline.decorate(Namespace("p1"))
    p2 = simple_pipeline.decorate(Namespace("p2"))
    p3 = simple_pipeline.decorate(Namespace("p3"))
    concat_node = PNode("array_concat")
    concat_nodes = {concat_node: ProcessorProps(SumArrays)}
    concat_dps: dict[PNode, set[PDependency]] = {
        concat_node: set(
            (
                PDependency(
                    p1,
                    in_arg=InParameter(
                        "arrays",
                        npt.NDArray[np.float64],
                        SumArrays.process,
                        InParameter.VAR_POSITIONAL,
                    ),
                    out_arg=OutParameter("output", npt.NDArray[np.float64]),
                ),
                PDependency(
                    p2,
                    in_arg=InParameter(
                        "arrays",
                        npt.NDArray[np.float64],
                        SumArrays.process,
                        InParameter.VAR_POSITIONAL,
                    ),
                    out_arg=OutParameter("output", npt.NDArray[np.float64]),
                ),
                PDependency(
                    p3,
                    in_arg=InParameter(
                        "arrays",
                        npt.NDArray[np.float64],
                        SumArrays.process,
                        InParameter.VAR_POSITIONAL,
                    ),
                    out_arg=OutParameter("output", npt.NDArray[np.float64]),
                ),
            )
        )
    }
    concat_pipeline = Pipeline(concat_nodes, concat_dps)
    return p1 + p2 + p3 + concat_pipeline


@pytest.fixture
def registry_of_singleton_factories() -> IRegistryOfSingletonFactories:
    return frozendict()


def test_simple_pipeline(
    simple_pipeline: Pipeline, registry_of_singleton_factories: IRegistryOfSingletonFactories
) -> None:
    session = PipelineSessionProvider.get_session(simple_pipeline, registry_of_singleton_factories)
    session.run()


def test_complex_pipeline(
    complex_pipeline: Pipeline, registry_of_singleton_factories: IRegistryOfSingletonFactories
) -> None:
    session = PipelineSessionProvider.get_session(
        complex_pipeline, registry_of_singleton_factories
    )
    session.run()
