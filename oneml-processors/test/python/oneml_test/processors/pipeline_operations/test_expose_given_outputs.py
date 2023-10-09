from oneml.processors.pipeline_operations import ExposeGivenOutputs
from oneml.processors.pipeline_operations._expose_given_outputs_processor import (
    ExposeGivenOutputsProcessor,
)


def test_expose_given_outputs_processor() -> None:
    outputs = {"foo": 1, "bar": "baz"}
    processor = ExposeGivenOutputsProcessor(outputs)
    assert processor.process() == outputs


def test_expose_given_outputs(expose_given_outputs: ExposeGivenOutputs) -> None:
    p = expose_given_outputs(
        outputs={"foo": 1, "bar": "baz"},
        out_collections={"col1": {"foo1": 1, "bar1": "baz"}, "col2": {"foo2": 1, "bar2": "baz"}},
    )

    assert set(p.inputs) == set()
    assert set(p.in_collections) == set()
    assert set(p.outputs) == {"foo", "bar"}
    assert set(p.out_collections) == {"col1", "col2"}
    assert set(p.out_collections.col1) == {"foo1", "bar1"}
    assert set(p.out_collections.col2) == {"foo2", "bar2"}
