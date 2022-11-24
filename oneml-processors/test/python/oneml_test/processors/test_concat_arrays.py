from typing import Any, Mapping, TypedDict

import numpy as np
import numpy.typing as npt
import pytest

from oneml.processors import (
    DAG,
    DagDependency,
    DagNode,
    InMethod,
    InProcessorParam,
    IProcess,
    Namespace,
    OutProcessorParam,
    ParamsRegistry,
    PipelineSessionProvider,
    ProcessorProps,
    frozendict,
)

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


@pytest.fixture
def storage() -> dict[str, npt.NDArray[np.float64]]:
    return {"a": np.array([10.0, 20.0, 30.0]), "b": np.array([-10.0, 20.0, -30.0])}


@pytest.fixture
def left_config(storage: dict[str, Any]) -> frozendict[str, Any]:
    return frozendict(storage=storage, url="a")


@pytest.fixture
def right_config(storage: dict[str, Any]) -> frozendict[str, Any]:
    return frozendict(storage=storage, url="b")


@pytest.fixture
def simple_pipeline(left_config: frozendict[str, Any], right_config: frozendict[str, Any]) -> DAG:
    left_arr = DagNode("left_arr")
    right_arr = DagNode("right_arr")
    multiply = DagNode("multiply")
    nodes = {
        left_arr: ProcessorProps(ArrayReader, left_config),
        right_arr: ProcessorProps(ArrayReader, right_config),
        multiply: ProcessorProps(ArrayDotProduct),
    }
    dependencies: dict[DagNode, tuple[DagDependency, ...]] = {
        multiply: (
            DagDependency(
                left_arr,
                in_arg=InProcessorParam("left", npt.NDArray[np.float64], InMethod.process),
                out_arg=OutProcessorParam("array", npt.NDArray[np.float64]),
            ),
            DagDependency(
                right_arr,
                in_arg=InProcessorParam("right", npt.NDArray[np.float64], InMethod.process),
                out_arg=OutProcessorParam("array", npt.NDArray[np.float64]),
            ),
        )
    }

    return DAG(nodes, dependencies)


@pytest.fixture
def complex_pipeline(simple_pipeline: DAG) -> DAG:
    p1 = simple_pipeline.decorate(Namespace("p1"))
    p2 = simple_pipeline.decorate(Namespace("p2"))
    p3 = simple_pipeline.decorate(Namespace("p3"))
    concat_node = DagNode("array_concat")
    concat_nodes = {concat_node: ProcessorProps(SumArrays)}
    concat_dps: dict[DagNode, tuple[DagDependency, ...]] = {
        concat_node: (
            DagDependency(
                DagNode("multiply", Namespace("p1")),
                in_arg=InProcessorParam(
                    "arrays",
                    npt.NDArray[np.float64],
                    InMethod.process,
                    InProcessorParam.VAR_POSITIONAL,
                ),
                out_arg=OutProcessorParam("output", npt.NDArray[np.float64]),
            ),
            DagDependency(
                DagNode("multiply", Namespace("p2")),
                in_arg=InProcessorParam(
                    "arrays",
                    npt.NDArray[np.float64],
                    InMethod.process,
                    InProcessorParam.VAR_POSITIONAL,
                ),
                out_arg=OutProcessorParam("output", npt.NDArray[np.float64]),
            ),
            DagDependency(
                DagNode("multiply", Namespace("p3")),
                in_arg=InProcessorParam(
                    "arrays",
                    npt.NDArray[np.float64],
                    InMethod.process,
                    InProcessorParam.VAR_POSITIONAL,
                ),
                out_arg=OutProcessorParam("output", npt.NDArray[np.float64]),
            ),
        )
    }
    concat_pipeline = DAG(concat_nodes, concat_dps)
    return p1 + p2 + p3 + concat_pipeline


@pytest.fixture
def params_registry() -> ParamsRegistry:
    return ParamsRegistry()


def test_simple_pipeline(simple_pipeline: DAG, params_registry: ParamsRegistry) -> None:
    session = PipelineSessionProvider.get_session(simple_pipeline, params_registry)
    session.run()


def test_complex_pipeline(complex_pipeline: DAG, params_registry: ParamsRegistry) -> None:
    session = PipelineSessionProvider.get_session(complex_pipeline, params_registry)
    session.run()
