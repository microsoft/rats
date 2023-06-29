from dataclasses import dataclass
from typing import Any, NamedTuple, TypedDict

import pytest

from oneml.processors import IProcess, Pipeline, PipelineBuilder, PipelineRunnerFactory, frozendict

########

# PROCESSORS (aka they do stuff; aka almost transformers)


@dataclass
class Array:
    x: list[float]


class ArrayReaderOutput(NamedTuple):
    array: Array


class ArrayReader(IProcess):
    def __init__(self, storage: dict[str, Array], url: str) -> None:
        super().__init__()
        self._storage = storage
        self._url = url

    def process(self) -> ArrayReaderOutput:
        return ArrayReaderOutput(array=self._storage[self._url])


ArrayDotProductOutput = TypedDict("ArrayDotProductOutput", {"result": float})


class ArrayProduct(IProcess):
    def process(self, left_arr: Array, right_arr: Array) -> ArrayDotProductOutput:
        return ArrayDotProductOutput(
            result=sum([xi * xj for xi, xj in zip(left_arr.x, right_arr.x)])
        )


SumFloatsOutput = TypedDict("SumFloatsOutput", {"result": float})


class SumFloats(IProcess):
    def process(self, *floats: float) -> SumFloatsOutput:
        return SumFloatsOutput(result=sum(floats))


########

# PARAM_GETTER


@pytest.fixture(scope="module")
def storage() -> dict[str, Array]:
    return {"a": Array([10.0, 20.0, 30.0]), "b": Array([-10.0, 20.0, -30.0])}


@pytest.fixture(scope="module")
def left_config(storage: dict[str, Array]) -> frozendict[str, Any]:
    return frozendict(storage=storage, url="a")


@pytest.fixture(scope="module")
def right_config(storage: dict[str, Array]) -> frozendict[str, Any]:
    return frozendict(storage=storage, url="b")


#######


# PIPELINE
@pytest.fixture(scope="module")
def pipeline(left_config: frozendict[str, Any], right_config: frozendict[str, Any]) -> Pipeline:
    left_reader = PipelineBuilder.task(ArrayReader, "left_reader", left_config)
    right_reader = PipelineBuilder.task(ArrayReader, "right_reader", right_config)
    product = PipelineBuilder.task(ArrayProduct, "array_product")

    w1 = PipelineBuilder.combine(
        pipelines=[left_reader, right_reader, product],
        name="w1",
        inputs={},
        outputs={"result": product.outputs.result},
        dependencies=(
            product.inputs.left_arr << left_reader.outputs.array,
            product.inputs.right_arr << right_reader.outputs.array,
        ),
    )
    w2 = PipelineBuilder.combine(
        pipelines=[left_reader, right_reader, product],
        name="w2",
        inputs={},
        outputs={"result": product.outputs.result},
        dependencies=(
            product.inputs.left_arr << left_reader.outputs.array,
            product.inputs.right_arr << right_reader.outputs.array,
        ),
    )
    w3 = PipelineBuilder.combine(
        pipelines=[left_reader, right_reader, product],
        inputs={},
        outputs={"result": product.outputs.result},
        dependencies=(
            product.inputs.left_arr << left_reader.outputs.array,
            product.inputs.right_arr << right_reader.outputs.array,
        ),
        name="w3",
    )
    sum_arrays = PipelineBuilder.task(SumFloats, "sum_floats")
    return PipelineBuilder.combine(
        pipelines=[sum_arrays, w1, w2, w3],
        inputs={},
        outputs={"result": sum_arrays.outputs.result},
        dependencies=(
            sum_arrays.inputs.floats << w1.outputs.result,
            sum_arrays.inputs.floats << w2.outputs.result,
            sum_arrays.inputs.floats << w3.outputs.result,
        ),
        name="p",
    )


def test_final_pipeline(
    pipeline_runner_factory: PipelineRunnerFactory, pipeline: Pipeline
) -> None:
    runner = pipeline_runner_factory(pipeline)
    outputs = runner()
    assert len(set(outputs)) == 1
    assert outputs["result"] == -1800


# Fails on devops b/c the graphviz binary is not available.
# TODO: install graphviz on build machines?
# def test_viz(pipeline: Pipeline) -> None:
#     pipeline_to_svg(pipeline)
