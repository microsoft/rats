from __future__ import annotations

import numpy as np
import pytest
from numpy.testing import assert_array_almost_equal

from oneml.assorted_processors.testing_processors import ArrayConcatenator, ArrayDotProduct
from oneml.processors.dag import DAG
from oneml.processors.processor import Processor
from oneml.processors.run_context import RunContext
from oneml.processors.run_in_subprocess import RunInSubProcess
from oneml.processors.topological_sort_dag_runner import TopologicalSortDAGRunner
from oneml.processors_pipeline_translation import PipelinesDAGRunner


@pytest.fixture(params=["topological", "pipelines"])
def dag_runner(request):
    if request.param == "topological":
        return TopologicalSortDAGRunner()
    elif request.param == "pipelines":
        return PipelinesDAGRunner()
    else:
        assert False


@pytest.fixture
def run_context(dag_runner):
    return RunContext(dag_runner)


@pytest.fixture
def simple_dag():
    dag = DAG(
        nodes=dict(
            multiply_a_b=ArrayDotProduct(),
            multiply_b_c=ArrayDotProduct(),
            concatenator=ArrayConcatenator(2),
        ),
        input_edges={
            "multiply_a_b.left": "a",
            "multiply_a_b.right": "b",
            "multiply_b_c.left": "b",
            "multiply_b_c.right": "c",
        },
        output_edges={"result": "concatenator.output"},
        edges={
            "concatenator.input0": "multiply_a_b.output",
            "concatenator.input1": "multiply_b_c.output",
        },
    )
    return dag


@pytest.fixture(params=["no-subprocesses", "subprocesses"])
def complex_dag(request, simple_dag):
    if request.param == "no-subprocesses":

        def wrap(processor: Processor) -> Processor:
            return processor

    elif request.param == "subprocesses":

        def wrap(processor: Processor) -> Processor:
            return RunInSubProcess(processor)

    else:
        assert False

    dag = DAG(
        nodes=dict(
            d1=simple_dag,
            d2=wrap(simple_dag),
            d3=wrap(simple_dag),
            concatenator_1=ArrayConcatenator(3),
            multiplier_1_2=ArrayDotProduct(),
            multiplier_2_3=wrap(ArrayDotProduct()),
            multiplier_1_3=ArrayDotProduct(),
            concatenator_2=wrap(ArrayConcatenator(3)),
        ),
        input_edges={
            "d1.a": "a1",
            "d1.b": "b1",
            "d1.c": "c1",
            "d2.a": "a2",
            "d2.b": "b2",
            "d2.c": "c2",
            "d3.a": "a3",
            "d3.b": "b3",
            "d3.c": "c3",
        },
        output_edges={
            "concat1": "concatenator_1.output",
            "concat2": "concatenator_2.output",
        },
        edges={
            "concatenator_1.input0": "d1.result",
            "concatenator_1.input1": "d2.result",
            "concatenator_1.input2": "d3.result",
            "multiplier_1_2.left": "d1.result",
            "multiplier_1_2.right": "d2.result",
            "multiplier_1_3.left": "d1.result",
            "multiplier_1_3.right": "d3.result",
            "multiplier_2_3.left": "d2.result",
            "multiplier_2_3.right": "d3.result",
            "concatenator_2.input0": "multiplier_1_2.output",
            "concatenator_2.input1": "multiplier_1_3.output",
            "concatenator_2.input2": "multiplier_2_3.output",
        },
    )
    return dag


def test_complex_dag(complex_dag: DAG, run_context: RunContext):
    rng = np.random.RandomState(34659120)
    a1 = rng.rand(4)
    b1 = rng.rand(4)
    c1 = rng.rand(4)
    a2 = rng.rand(10)
    b2 = rng.rand(10)
    c2 = rng.rand(10)
    a3 = rng.rand(7)
    b3 = rng.rand(7)
    c3 = rng.rand(7)

    d1 = np.hstack((np.dot(a1, b1), np.dot(b1, c1)))
    d2 = np.hstack((np.dot(a2, b2), np.dot(b2, c2)))
    d3 = np.hstack((np.dot(a3, b3), np.dot(b3, c3)))

    concat1 = np.concatenate((d1, d2, d3))

    m12 = np.dot(d1, d2)
    m23 = np.dot(d2, d3)
    m13 = np.dot(d1, d3)

    concat2 = np.hstack((m12, m13, m23))

    outputs = complex_dag.process(
        run_context=run_context,
        a1=a1,
        a2=a2,
        a3=a3,
        b1=b1,
        b2=b2,
        b3=b3,
        c1=c1,
        c2=c2,
        c3=c3,
    )
    assert len(outputs) == 2
    assert_array_almost_equal(outputs.concat1, concat1)
    assert_array_almost_equal(outputs.concat2, concat2)
