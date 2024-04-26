from ._complex_pipeline import ExampleComplexPipelineServices
from ._lr_pipeline_container import LRPipelineServices
from ._simple_typed_pipeline import ExampleSimpleTypedPipelineServices
from ._simple_untyped_pipeline import ExampleSimpleUntypedPipelineServices


class Services:
    DUMMY_UNTYPED_TRAIN_PIPELINE = ExampleSimpleUntypedPipelineServices.TRAIN_PIPELINE
    DUMMY_TRAIN_PIPELINE = ExampleSimpleTypedPipelineServices.TRAIN_PIPELINE
    DUMMY_TRAIN_AND_TEST_PIPELINE = ExampleComplexPipelineServices.TRAIN_AND_TEST_PIPELINE
    DUMMY_LOAD_DATA = ExampleSimpleTypedPipelineServices.LOAD_DATA
    DUMMY_TRAIN_MODEL = ExampleSimpleTypedPipelineServices.TRAIN_MODEL
    LR_TRAIN_PIPELINE = LRPipelineServices.TRAIN_PIPELINE
    LR_PREDICT_PIPELINE = LRPipelineServices.PREDICT_PIPELINE
