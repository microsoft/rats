from rats.processors._legacy.pipeline_operations import ExposeGivenOutputs
from rats.processors._legacy.pipeline_operations._expose_given_outputs_processor import (
    ExposeGivenOutputsProcessor,
)


def test_expose_given_outputs_processor() -> None:
    outputs = {"foo": 1, "bar": "baz"}
    processor = ExposeGivenOutputsProcessor(outputs)
    assert processor.process() == outputs


def test_expose_given_outputs(expose_given_outputs: ExposeGivenOutputs) -> None:
    p = expose_given_outputs(
        outputs={
            "foo": 1,
            "bar": "baz",
            "col1.foo1": 1,
            "col1.bar1": "baz",
            "col2.foo2": 1,
            "col2.bar2": "baz",
        }
    )

    assert set(p.inputs) == set()
    assert set(p.outputs) == {"foo", "bar", "col1", "col2"}
    assert set(p.outputs.col1) == {"foo1", "bar1"}
    assert set(p.outputs.col2) == {"foo2", "bar2"}
