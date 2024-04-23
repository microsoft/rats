from rats import apps
from rats import processors as rp
from rats.processors import ux

from ._simple_typed_pipeline import (
    ExampleSimpleTypedPipelineServices,
    TestPipeline,
    TrainPipeline,
)


class ExampleComplexPipelineBuilder(rp.PipelineContainer):
    _app: apps.Container

    def __init__(self, app: apps.Container):
        self._app = app

    @rp.pipeline
    def train_pipeline(self) -> TrainPipeline:
        return self._app.get(ExampleSimpleTypedPipelineServices.TRAIN_PIPELINE)

    @rp.pipeline
    def test_pipeline(self) -> TestPipeline:
        return self._app.get(ExampleSimpleTypedPipelineServices.TEST_PIPELINE)

    @rp.pipeline
    def train_and_test_pipeline(self) -> ux.UPipeline:
        train = (
            self.train_pipeline()
            .rename_inputs(dict(url="url.train"))
            .rename_outputs(dict(message="message.train"))
        )
        test = (
            self.test_pipeline()
            .rename_inputs(dict(url="url.test"))
            .rename_outputs(dict(message="message.test"))
        )
        return self.combine([train, test], dependencies=[train >> test])


class ExampleComplexPipelineServices:
    TRAIN_AND_TEST_PIPELINE = apps.method_service_id(
        ExampleComplexPipelineBuilder.train_and_test_pipeline
    )
