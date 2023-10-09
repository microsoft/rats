import pytest

from oneml.processors.pipeline_operations._duplicate_pipeline import DuplicatePipeline
from oneml.processors.ux import UPipeline


def test_duplicate_pipeline(
    pipeline_for_tests: UPipeline, duplicate_pipeline: DuplicatePipeline
) -> None:
    pipeline = pipeline_for_tests
    copy_names = ["copy1", "copy2"]
    broadcast_inputs = ["input1"]
    duplicated_pipeline = duplicate_pipeline(
        pipeline=pipeline, copy_names=copy_names, broadcast_inputs=broadcast_inputs
    )

    # Test pipeline name
    assert duplicated_pipeline.name == pipeline.name

    # Test inputs
    assert set(duplicated_pipeline.inputs) == set()
    assert set(duplicated_pipeline.in_collections) == {"u", "v", "w", "x"}
    assert set(duplicated_pipeline.in_collections.u) == {"copy1", "copy2"}
    assert set(duplicated_pipeline.in_collections.v) == {"copy1", "copy2"}
    assert set(duplicated_pipeline.in_collections.w) == {
        "copy1_a",
        "copy2_a",
        "copy1_b",
        "copy2_b",
    }
    assert set(duplicated_pipeline.in_collections.x) == {"copy1_k", "copy2_k"}

    # Test outputs
    assert set(duplicated_pipeline.outputs) == set()
    assert set(duplicated_pipeline.out_collections) == {"a", "b", "c", "d"}
    assert set(duplicated_pipeline.out_collections.a) == {"copy1", "copy2"}
    assert set(duplicated_pipeline.out_collections.b) == {"copy1", "copy2"}
    assert set(duplicated_pipeline.out_collections.c) == {
        "copy1_a",
        "copy2_a",
        "copy1_b",
        "copy2_b",
    }
    assert set(duplicated_pipeline.out_collections.d) == {"copy1_a", "copy2_a"}
