from collections.abc import Sequence
from typing import TypedDict

import pytest

from rats.processors.dag import IProcess
from rats.processors.ux import CombinedPipeline, PipelineRunnerFactory, Task, UPipeline


class AccOutput(TypedDict):
    acc: float


class Acc(IProcess):
    def process(self) -> AccOutput:
        return AccOutput(acc=0.0)


class ReportGenerator(IProcess):
    def process(self, accs: Sequence[float]) -> None: ...


@pytest.fixture
def acc1() -> UPipeline:
    return Task(Acc, "acc1")


@pytest.fixture
def acc2() -> UPipeline:
    return Task(Acc, "acc2")


@pytest.fixture
def report() -> UPipeline:
    return Task(ReportGenerator, "report")


def test_gather_inputs_to_single_output(
    pipeline_runner_factory: PipelineRunnerFactory, acc1: UPipeline, acc2: UPipeline
) -> None:
    # OutPort | OutPort -> OutPort
    p: UPipeline = CombinedPipeline(
        pipelines=[acc1, acc2],
        name="p",
        outputs={"acc": acc1.outputs.acc | acc2.outputs.acc},
    )
    assert len(p.outputs) == 1
    assert len(p.outputs.acc) == 1
    assert p.outputs.acc[0].param.annotation == tuple[float, ...]

    runner = pipeline_runner_factory(p)
    outputs = runner()
    assert set(outputs) == set(("acc",))
    assert outputs.acc == (0.0, 0.0)

    p = CombinedPipeline(
        pipelines=[acc1, acc2],
        name="p",
        outputs={"acc.nested": acc1.outputs.acc | acc2.outputs.acc},
    )
    assert len(p.outputs) == 1
    assert len(p.outputs.acc) == 1
    assert len(p.outputs.acc.nested) == 1
    assert p.outputs.acc.nested[0].param.annotation == tuple[float, ...]

    runner = pipeline_runner_factory(p)
    outputs = runner()
    assert set(outputs) == set(("acc",))
    assert outputs.acc.nested == (0.0, 0.0)
