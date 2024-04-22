from typing import Any

from rats import apps
from rats import pipelines_app as rpa
from rats.processors import ux

from ._simple_typed_pipeline import (
    ExampleSimpleTypedPipelineServices,
    TestPipeline,
    TrainPipeline,
)


class ExampleComplexPipelineBuilder(rpa.PipelineContainer):
    _app: apps.Container

    def __init__(self, app: apps.Container):
        self._app = app

    @rpa.pipeline
    def train_pipeline(self) -> TrainPipeline:
        return self._app.get(ExampleSimpleTypedPipelineServices.TRAIN_PIPELINE)

    @rpa.pipeline
    def test_pipeline(self) -> TestPipeline:
        return self._app.get(ExampleSimpleTypedPipelineServices.TEST_PIPELINE)

    @rpa.pipeline
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

    @apps.group(rpa.PipelineRegistryGroups.EXECUTABLE_PIPELINES)
    def executable_pipeline(self) -> Any:
        return (
            dict(
                name="train_and_test_pipeline",
                doc="Example pipeline 3",
                service_id=apps.autoid(self.train_and_test_pipeline),
            ),
        )


class ExampleComplexPipelineServices:
    TRAIN_AND_TEST_PIPELINE = apps.autoid(ExampleComplexPipelineBuilder.train_and_test_pipeline)
