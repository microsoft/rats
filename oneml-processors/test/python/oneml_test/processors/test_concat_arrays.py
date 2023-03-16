from dataclasses import dataclass
from typing import Any, Mapping, TypedDict

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
    PipelineSessionProvider,
    ProcessorProps,
    frozendict,
)


@dataclass
class Array:
    x: list[float]


ArrayReaderOutput = TypedDict("ArrayReaderOutput", {"array": Array})
ArrayDotProductOutput = TypedDict("ArrayDotProductOutput", {"output": float})
SumFloatsOutput = TypedDict("SumFloatsOutput", {"output": float})


class ArrayReader(IProcess):
    def __init__(self, storage: Mapping[str, Array], url: str) -> None:
        super().__init__()
        self._storage = storage
        self._url = url

    def process(self) -> ArrayReaderOutput:
        return ArrayReaderOutput(array=self._storage[self._url])


class ArrayDotProduct(IProcess):
    def process(self, left: Array, right: Array) -> ArrayDotProductOutput:
        return ArrayDotProductOutput(output=sum([xi * xj for xi, xj in zip(left.x, right.x)]))


class SumFloats(IProcess):
    def process(self, *nums: float) -> SumFloatsOutput:
        return SumFloatsOutput(output=sum(nums))


@pytest.fixture
def storage() -> dict[str, Array]:
    return {"a": Array([10.0, 20.0, 30.0]), "b": Array([-10.0, 20.0, -30.0])}


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
                in_arg=InProcessorParam("left", Array, InMethod.process),
                out_arg=OutProcessorParam("array", Array),
            ),
            DagDependency(
                right_arr,
                in_arg=InProcessorParam("right", Array, InMethod.process),
                out_arg=OutProcessorParam("array", Array),
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
    concat_nodes = {concat_node: ProcessorProps(SumFloats)}
    concat_dps: dict[DagNode, tuple[DagDependency, ...]] = {
        concat_node: (
            DagDependency(
                DagNode("multiply", Namespace("p1")),
                in_arg=InProcessorParam(
                    "arrays",
                    Array,
                    InMethod.process,
                    InProcessorParam.VAR_POSITIONAL,
                ),
                out_arg=OutProcessorParam("output", Array),
            ),
            DagDependency(
                DagNode("multiply", Namespace("p2")),
                in_arg=InProcessorParam(
                    "arrays",
                    Array,
                    InMethod.process,
                    InProcessorParam.VAR_POSITIONAL,
                ),
                out_arg=OutProcessorParam("output", Array),
            ),
            DagDependency(
                DagNode("multiply", Namespace("p3")),
                in_arg=InProcessorParam(
                    "arrays",
                    Array,
                    InMethod.process,
                    InProcessorParam.VAR_POSITIONAL,
                ),
                out_arg=OutProcessorParam("output", Array),
            ),
        )
    }
    concat_pipeline = DAG(concat_nodes, concat_dps)
    return p1 + p2 + p3 + concat_pipeline


def test_simple_pipeline(
    pipeline_session_provider: PipelineSessionProvider,
    simple_pipeline: DAG,
) -> None:
    session = pipeline_session_provider.get_session(simple_pipeline)
    session.run()


def test_complex_pipeline(
    pipeline_session_provider: PipelineSessionProvider,
    complex_pipeline: DAG,
) -> None:
    session = pipeline_session_provider.get_session(complex_pipeline)
    session.run()
