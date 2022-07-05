from __future__ import annotations

from typing import Any, Dict

import numpy as np
import numpy.typing as npt
import pytest

from oneml.assorted_processors.testing_processors import ArrayConcatenator, ArrayDotProduct
from oneml.processors import dag
from oneml.processors.dag import DAG
from oneml.processors.dag_flattener import DAGFlattener
from oneml.processors.processor_using_signature_decorator import processor_using_signature
from oneml.processors.return_annotation import Output
from oneml.processors.run_context import RunContext
from oneml.processors.topological_sort_dag_runner import TopologicalSortDAGRunner
from oneml.processors_pipeline_translation import PipelinesDAGRunner


@processor_using_signature
class ArrayReader:
    """Mock for a source node that reads an array."""

    def __init__(self, storage: Dict[str, Any], url: str):
        self.storage = storage
        self.url = url

    def _process(self) -> Output(output=npt.ArrayLike):
        return dict(output=self.storage[self.url])


@processor_using_signature
class ArrayWriter:
    """Mock for a sink node that write an array."""

    def __init__(self, storage: Dict[str, Any], url: str) -> None:
        self.storage = storage
        self.url = url

    def _process(self, input: npt.ArrayLike) -> Output():
        self.storage[self.url] = input
        return dict()


@pytest.fixture
def dag_flattener():
    return DAGFlattener()


@pytest.fixture(params=["topological", "pipelines"])
def dag_runner(request, dag_flattener):
    if request.param == "topological":
        return TopologicalSortDAGRunner(dag_flattener=dag_flattener)
    elif request.param == "pipelines":
        return PipelinesDAGRunner(dag_flattener=dag_flattener)
    else:
        assert False


@pytest.fixture
def run_context(dag_runner):
    return RunContext(dag_runner)


@pytest.fixture
def storage():
    return dict(
        a=np.array([10.0, 20.0, 30.0]),
        b=np.array([-10.0, 20.0, -30.0]),
    )


@pytest.fixture
def simple_dag(storage):
    dag = DAG(
        nodes=dict(
            load_left=ArrayReader(storage, "a"),
            multiply=ArrayDotProduct(),
            write=ArrayWriter(storage, "r"),
        ),
        input_edges={
            "multiply.right": "right",
        },
        output_edges={"result": "multiply.output"},
        edges={"multiply.left": "load_left.output", "write.input": "multiply.output"},
    )
    return dag


@pytest.fixture
def complex_dag(storage, simple_dag):
    dag = DAG(
        nodes=dict(
            load_right=ArrayReader(storage, "b"),
            d1=simple_dag,
            d2=simple_dag,
            d3=simple_dag,
            concatenator=ArrayConcatenator(3),
            write=ArrayWriter(storage, "r"),
        ),
        input_edges={},
        output_edges={},
        edges={
            "d1.right": "load_right.output",
            "d2.right": "load_right.output",
            "d3.right": "load_right.output",
            "concatenator.input0": "d1.result",
            "concatenator.input1": "d2.result",
            "concatenator.input2": "d3.result",
            "write.input": "concatenator.output",
        },
    )
    return dag


def test_flatten_simple_dag(simple_dag: DAG, dag_flattener: DAGFlattener):
    assert simple_dag.get_input_schema() == dict(
        right=npt.ArrayLike,
    )
    assert simple_dag.get_output_schema() == dict(result=npt.ArrayLike)
    flattened = dag_flattener.flatten(simple_dag)
    assert simple_dag.nodes == flattened.nodes
    assert simple_dag.input_edges == flattened.input_edges
    assert simple_dag.output_edges == flattened.output_edges
    assert simple_dag.edges == flattened.edges
    assert simple_dag.get_input_schema() == flattened.get_input_schema()
    assert simple_dag.get_output_schema() == flattened.get_output_schema()


def test_process_simple_dag(simple_dag: DAG, run_context: RunContext, storage: Dict[str, Any]):
    outputs = simple_dag.process(
        run_context=run_context,
        right=np.array([-1, -2, -3]),
    )
    assert len(outputs) == 1
    assert outputs["result"] == -140
    assert storage["r"] is outputs["result"]


def test_flatten_complex_dag(simple_dag: DAG, complex_dag: DAG, dag_flattener: DAGFlattener):
    assert complex_dag.get_input_schema() == dict()
    assert complex_dag.get_output_schema() == dict()
    flattened = dag_flattener.flatten(complex_dag)
    assert flattened.nodes == {
        "load_right": complex_dag.nodes["load_right"],
        "d1/load_left": simple_dag.nodes["load_left"],
        "d1/multiply": simple_dag.nodes["multiply"],
        "d1/write": simple_dag.nodes["write"],
        "d2/load_left": simple_dag.nodes["load_left"],
        "d2/multiply": simple_dag.nodes["multiply"],
        "d2/write": simple_dag.nodes["write"],
        "d3/load_left": simple_dag.nodes["load_left"],
        "d3/multiply": simple_dag.nodes["multiply"],
        "d3/write": simple_dag.nodes["write"],
        "concatenator": complex_dag.nodes["concatenator"],
        "write": complex_dag.nodes["write"],
    }
    assert flattened.input_edges == {}
    assert flattened.output_edges == {}
    assert flattened.edges == {
        "d1/multiply.left": "d1/load_left.output",
        "d1/write.input": "d1/multiply.output",
        "d1/multiply.right": "load_right.output",
        "concatenator.input0": "d1/multiply.output",
        "d2/multiply.left": "d2/load_left.output",
        "d2/write.input": "d2/multiply.output",
        "d2/multiply.right": "load_right.output",
        "concatenator.input1": "d2/multiply.output",
        "d3/multiply.left": "d3/load_left.output",
        "d3/write.input": "d3/multiply.output",
        "d3/multiply.right": "load_right.output",
        "concatenator.input2": "d3/multiply.output",
        "write.input": "concatenator.output",
    }


def test_process_complex_dag(complex_dag: DAG, run_context: RunContext, storage: Dict[str, Any]):
    outputs = complex_dag.process(
        run_context=run_context,
    )
    assert len(outputs) == 0
    assert (storage["r"] == np.array([-600, -600, -600])).all()
