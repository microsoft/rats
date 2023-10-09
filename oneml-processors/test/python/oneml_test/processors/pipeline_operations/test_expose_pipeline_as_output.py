from oneml.processors.pipeline_operations import ITransformPipeline
from oneml.processors.ux import UPipeline


def test_expose_self_pipeline(
    pipeline_for_tests: UPipeline, expose_pipeline_as_output: ITransformPipeline
) -> None:
    pipeline = pipeline_for_tests
    with_exposed_pipeline = expose_pipeline_as_output(pipeline)

    # Test pipeline name
    assert with_exposed_pipeline.name == pipeline.name

    # Test inputs
    assert set(with_exposed_pipeline.inputs) == set(pipeline.inputs)
    assert set(with_exposed_pipeline.in_collections) == set(pipeline.in_collections)
    assert set(with_exposed_pipeline.outputs) == set(pipeline.outputs) | {"pipeline"}
    assert set(with_exposed_pipeline.out_collections) == set(pipeline.out_collections)
