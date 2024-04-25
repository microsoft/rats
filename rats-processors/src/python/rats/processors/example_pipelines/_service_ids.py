from ._complex_pipeline import ExampleComplexPipelineServices
from ._simple_typed_pipeline import ExampleSimpleTypedPipelineServices
from ._simple_untyped_pipeline import ExampleSimpleUntypedPipelineServices


class Services:
    UNTYPED_TRAIN_PIPELINE = ExampleSimpleUntypedPipelineServices.TRAIN_PIPELINE
    TRAIN_PIPELINE = ExampleSimpleTypedPipelineServices.TRAIN_PIPELINE
    TRAIN_AND_TEST_PIPELINE = ExampleComplexPipelineServices.TRAIN_AND_TEST_PIPELINE
    LOAD_DATA = ExampleSimpleTypedPipelineServices.LOAD_DATA
    TRAIN_MODEL = ExampleSimpleTypedPipelineServices.TRAIN_MODEL
