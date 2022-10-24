from typing import Mapping, TypedDict

import numpy as np
import numpy.typing as npt
import pytest

from oneml.processors import (
    IGetParams,
    IProcess,
    ParamsRegistry,
    Workflow,
    WorkflowClient,
    WorkflowRunner,
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

storage = {"a": np.array([10.0, 20.0, 30.0]), "b": np.array([-10.0, 20.0, -30.0])}
left_config: IGetParams = frozendict(storage=storage, url="a")
right_config: IGetParams = frozendict(storage=storage, url="b")


#######

# PIPELINE
@pytest.fixture
def workflow() -> Workflow:
    left_reader = WorkflowClient.single_task("left_reader", ArrayReader, left_config)
    right_reader = WorkflowClient.single_task("right_reader", ArrayReader, right_config)
    product = WorkflowClient.single_task("array_product", ArrayProduct)

    w1 = WorkflowClient.compose_workflow(
        name="w1",
        workflows=(left_reader, right_reader, product),
        dependencies=(
            product.sig.left_arr << left_reader.ret.array,
            product.sig.right_arr << right_reader.ret.array,
        ),
    )
    w2 = WorkflowClient.compose_workflow(
        name="w2",
        workflows=(left_reader, right_reader, product),
        dependencies=(
            product.sig.left_arr << left_reader.ret.array,
            product.sig.right_arr << right_reader.ret.array,
        ),
    )
    w3 = WorkflowClient.compose_workflow(
        name="w3",
        workflows=(left_reader, right_reader, product),
        dependencies=(
            product.sig.left_arr << left_reader.ret.array,
            product.sig.right_arr << right_reader.ret.array,
        ),
    )
    sum_arrays = WorkflowClient.single_task("sum_arrays", SumArrays)
    return WorkflowClient.compose_workflow(
        "p",
        (sum_arrays, w1, w2, w3),
        dependencies=(
            sum_arrays.sig.arrays << w1.ret.result,
            sum_arrays.sig.arrays << w2.ret.result,
            sum_arrays.sig.arrays << w3.ret.result,
        ),
    )


@pytest.fixture
def params_registry() -> ParamsRegistry:
    return ParamsRegistry()


def test_final_workflow(workflow: Workflow, params_registry: ParamsRegistry) -> None:
    runner = WorkflowRunner(workflow, params_registry)
    outputs = runner()
    assert len(set(outputs)) == 1
    assert outputs["result"] == -1800
