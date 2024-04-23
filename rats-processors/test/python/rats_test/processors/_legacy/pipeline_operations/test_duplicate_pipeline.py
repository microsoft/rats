from rats.processors._legacy.pipeline_operations._duplicate_pipeline import DuplicatePipeline
from rats.processors._legacy.ux import UPipeline


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
    assert set(duplicated_pipeline.inputs) == {"u", "v", "w", "x"}
    assert set(duplicated_pipeline.inputs.u) == {"copy1", "copy2"}
    assert set(duplicated_pipeline.inputs.v) == {"copy1", "copy2"}
    assert set(duplicated_pipeline.inputs.w) == {
        "a_copy1",
        "a_copy2",
        "b_copy1",
        "b_copy2",
    }
    assert set(duplicated_pipeline.inputs.x) == {"k_copy1", "k_copy2"}

    # Test outputs
    assert set(duplicated_pipeline.outputs) == {"a", "b", "c", "d"}
    assert set(duplicated_pipeline.outputs.a) == {"copy1", "copy2"}
    assert set(duplicated_pipeline.outputs.b) == {"copy1", "copy2"}
    assert set(duplicated_pipeline.outputs.c) == {
        "a_copy1",
        "a_copy2",
        "b_copy1",
        "b_copy2",
    }
    assert set(duplicated_pipeline.outputs.d) == {"a_copy1", "a_copy2"}
