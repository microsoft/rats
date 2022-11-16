from typing import Mapping, TypedDict

import numpy as np
import numpy.typing as npt
import pytest

from oneml.processors import (
    IGetParams,
    IProcess,
    ParamsRegistry,
    Pipeline,
    PipelineBuilder,
    PipelineRunner,
    frozendict,
)

########

# PROCESSORS (aka they do stuff; aka almost transformers)

ArrayReaderOutput = TypedDict("ArrayReaderOutput", {"array": npt.NDArray[np.float64]})


class ArrayReader(IProcess):
    def __init__(self, storage: Mapping[str, npt.NDArray[np.float64]], url: str) -> None:
        super().__init__()
        self._storage = storage
        self._url = url

    def process(self) -> ArrayReaderOutput:
        return ArrayReaderOutput(array=self._storage[self._url])


ArrayDotProductOutput = TypedDict("ArrayDotProductOutput", {"result": npt.NDArray[np.float64]})


class ArrayProduct(IProcess):
    def process(
        self, left_arr: npt.NDArray[np.float64], right_arr: npt.NDArray[np.float64]
    ) -> ArrayDotProductOutput:
        return ArrayDotProductOutput(result=np.dot(left_arr, right_arr))


SumArraysOutput = TypedDict("SumArraysOutput", {"result": npt.NDArray[np.float64]})


class SumArrays(IProcess):
    def process(self, *arrays: npt.NDArray[np.float64]) -> SumArraysOutput:
        return SumArraysOutput(result=np.sum([np.sum(a) for a in arrays]))


########

# PARAM_GETTER


@pytest.fixture(scope="module")
def storage() -> dict[str, npt.NDArray[np.float64]]:
    return {"a": np.array([10.0, 20.0, 30.0]), "b": np.array([-10.0, 20.0, -30.0])}


@pytest.fixture(scope="module")
def left_config(storage: dict[str, npt.NDArray[np.float64]]) -> IGetParams:
    return frozendict(storage=storage, url="a")


@pytest.fixture(scope="module")
def right_config(storage: dict[str, npt.NDArray[np.float64]]) -> IGetParams:
    return frozendict(storage=storage, url="b")


#######

# PIPELINE
@pytest.fixture(scope="module")
def pipeline(left_config: IGetParams, right_config: IGetParams) -> Pipeline:
    left_reader = PipelineBuilder.task("left_reader", ArrayReader, left_config)
    right_reader = PipelineBuilder.task("right_reader", ArrayReader, right_config)
    product = PipelineBuilder.task("array_product", ArrayProduct)

    w1 = PipelineBuilder.combine(
        left_reader,
        right_reader,
        product,
        inputs={},
        outputs={"result": product.outputs.result},
        dependencies=(
            product.inputs.left_arr << left_reader.outputs.array,
            product.inputs.right_arr << right_reader.outputs.array,
        ),
        name="w1",
    )
    w2 = PipelineBuilder.combine(
        left_reader,
        right_reader,
        product,
        inputs={},
        outputs={"result": product.outputs.result},
        dependencies=(
            product.inputs.left_arr << left_reader.outputs.array,
            product.inputs.right_arr << right_reader.outputs.array,
        ),
        name="w2",
    )
    w3 = PipelineBuilder.combine(
        left_reader,
        right_reader,
        product,
        inputs={},
        outputs={"result": product.outputs.result},
        dependencies=(
            product.inputs.left_arr << left_reader.outputs.array,
            product.inputs.right_arr << right_reader.outputs.array,
        ),
        name="w3",
    )
    sum_arrays = PipelineBuilder.task("sum_arrays", SumArrays)
    return PipelineBuilder.combine(
        sum_arrays,
        w1,
        w2,
        w3,
        inputs={},
        outputs={"result": sum_arrays.outputs.result},
        dependencies=(
            sum_arrays.inputs.arrays << w1.outputs.result,
            sum_arrays.inputs.arrays << w2.outputs.result,
            sum_arrays.inputs.arrays << w3.outputs.result,
        ),
        name="p",
    )


@pytest.fixture(scope="module")
def params_registry() -> ParamsRegistry:
    return ParamsRegistry()


def test_final_pipeline(pipeline: Pipeline, params_registry: ParamsRegistry) -> None:
    runner = PipelineRunner(pipeline, params_registry)
    outputs = runner()
    assert len(set(outputs)) == 1
    assert outputs["result"] == -1800


# Fails on devops b/c the graphviz binary is not available.
# TODO: install graphviz on build machines?
# def test_viz(pipeline: Pipeline) -> None:
#     pipeline_to_svg(pipeline)
