from typing import Sequence, TypedDict

import pytest

from oneml.processors import CombinedPipeline, IProcess, Pipeline, Task
from oneml.processors.utils import frozendict
from oneml.processors.ux import PipelineRunner

AccOutput = TypedDict("AccOutput", {"acc": float})


class Acc(IProcess):
    def process(self) -> AccOutput:
        return AccOutput(acc=0.0)


class ReportGenerator(IProcess):
    def process(self, accs: Sequence[float]) -> None:
        ...


@pytest.fixture
def acc1() -> Pipeline:
    return Task(Acc, "acc1")


@pytest.fixture
def acc2() -> Pipeline:
    return Task(Acc, "acc2")


@pytest.fixture
def report() -> Pipeline:
    return Task(ReportGenerator, "report")


def test_gather_inputs_to_single_output(acc1: Pipeline, acc2: Pipeline) -> None:
    # OutEntry | OutEntry -> OutEntry
    p = CombinedPipeline(
        acc1,
        acc2,
        name="p",
        outputs={"acc": acc1.outputs.acc | acc2.outputs.acc},
    )
    assert len(p.outputs) == 1
    assert len(p.outputs.acc) == 1
    assert p.outputs.acc[0].param.annotation == tuple[float, ...]

    runner = PipelineRunner(p)
    outputs = runner()
    assert set(outputs) == set(("acc",))
    assert outputs.acc == (0.0, 0.0)

    # OutEntry | OutEntry -> OutCollection.OutEntry
    p = CombinedPipeline(
        acc1,
        acc2,
        name="p",
        outputs={"acc.nested": acc1.outputs.acc | acc2.outputs.acc},
    )
    assert len(p.outputs) == 0
    assert len(p.out_collections) == 1
    assert len(p.out_collections.acc) == 1
    assert len(p.out_collections.acc.nested) == 1
    assert p.out_collections.acc.nested[0].param.annotation == tuple[float, ...]

    runner = PipelineRunner(p)
    outputs = runner()
    assert set(outputs) == set(("acc",))
    assert outputs.acc == frozendict(nested=(0.0, 0.0))
