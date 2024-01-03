from __future__ import annotations

from typing import TypedDict

import pytest

from oneml.processors.ux import CombinedPipeline, PipelineRunnerFactory, UPipeline, UTask


class Outputs(TypedDict):
    d: str


class Processor1:
    def __init__(self, a: int, b: str = "aaa") -> None:
        self._a = a
        self._b = b

    def process(self, c: str) -> Outputs:
        return dict(d=f"{self._a},{self._b},{c}")


class Processor2:
    def __init__(self, b: str = "kkk") -> None:
        self._b = b

    def process(self) -> Outputs:
        return dict(d=self._b)


class Processor3:
    def __init__(self, b: str) -> None:
        self._b = b

    def process(self) -> Outputs:
        return dict(d=self._b)


def test_task_with_default_values(pipeline_runner_factory: PipelineRunnerFactory) -> None:
    p = UTask(Processor1, config=dict(a=10))
    r = pipeline_runner_factory(p)

    # Not setting b.  The default value should be used.
    o = r(dict(c="ccc"))
    assert o.d == "10,aaa,ccc"

    # Setting b in the runner inputs.  The given value should be used.
    o = r(dict(c="ccc", b="ddd"))
    assert o.d == "10,ddd,ccc"

    # Setting b in the config.  The given value should be used.
    p = UTask(Processor1, config=dict(a=10, b="bbb"))
    r = pipeline_runner_factory(p)
    o = r(dict(c="ccc"))
    assert o.d == "10,bbb,ccc"

    # Setting b in the runner inputs after it was set in config should result in an error because
    # it is not an input of the pipeline.
    with pytest.raises(KeyError):
        o = r(dict(b="qqq", c="ccc"))

    # Not setting c in the runner inputs should fail b/c it does not have a default.
    with pytest.raises(ValueError) as ex:
        o = r()
    assert str(ex.value) == "Missing pipeline inputs: {'c'}."

    # Not setting a in the config and in the runner inputs should fail b/c is it a process input.
    p = UTask(Processor1)
    r = pipeline_runner_factory(p)

    with pytest.raises(ValueError) as ex:
        o = r(dict(c="ccc"))
    assert str(ex.value) == "Missing pipeline inputs: {'a'}."


def test_combined_pipeline_with_default_values(
    pipeline_runner_factory: PipelineRunnerFactory,
) -> None:
    p1 = UTask(Processor1, config=dict(a=10))
    p2 = UTask(Processor2)

    p: UPipeline = CombinedPipeline(
        [p1, p2],
        name="p",
        outputs={"d.p1": p1.outputs.d, "d.p2": p2.outputs.d},
    )

    assert set(p.inputs) == set(("b", "c"))
    assert set(p.out_collections) == set(("d",))
    assert set(p.out_collections.d) == set(("p1", "p2"))

    r = pipeline_runner_factory(p)

    # Not setting b.  Each processor should use its own default.
    o = r(dict(c="ccc"))
    assert o.d.p1 == "10,aaa,ccc"
    assert o.d.p2 == "kkk"

    # Setting b in the runner inputs.  All processors should use the given value.
    o = r(dict(c="ccc", b="bbb"))
    assert o.d.p1 == "10,bbb,ccc"
    assert o.d.p2 == "bbb"

    # Adding a processor with no default value for b.
    p3 = UTask(Processor3)
    p4: UPipeline = CombinedPipeline(
        [p1, p2, p3],
        name="p4",
        outputs={"d.p1": p1.outputs.d, "d.p2": p2.outputs.d, "d.p3": p3.outputs.d},
    )

    r = pipeline_runner_factory(p4)

    # Setting b in the runner inputs.  All processors should use the given value.
    o = r(dict(c="ccc", b="bbb"))
    assert o.d.p1 == "10,bbb,ccc"
    assert o.d.p2 == "bbb"
    assert o.d.p3 == "bbb"

    # Not setting b.  There should be an error b/c if even one processor needs it, it is required.
    with pytest.raises(ValueError) as ex:
        o = r(dict(c="ccc"))
    assert str(ex.value) == "Missing pipeline inputs: {'b'}."

    # Providing the value for p3's b in the config.
    p3 = UTask(Processor3, config=dict(b="mmm"))
    p5: UPipeline = CombinedPipeline(
        [p1, p2, p3],
        name="p5",
        outputs={"d.p1": p1.outputs.d, "d.p2": p2.outputs.d, "d.p3": p3.outputs.d},
    )

    # Not setting b, p1 an p2 should use their defaults, p3 should use the config value.
    r = pipeline_runner_factory(p5)
    o = r(dict(c="ccc"))
    assert o.d.p1 == "10,aaa,ccc"
    assert o.d.p2 == "kkk"
    assert o.d.p3 == "mmm"

    # Setting b in the runner inputs.  p1 and p2 should use the given value, p3 should use its
    # config value.
    o = r(dict(c="ccc", b="bbb"))
    assert o.d.p1 == "10,bbb,ccc"
    assert o.d.p2 == "bbb"
    assert o.d.p3 == "mmm"
