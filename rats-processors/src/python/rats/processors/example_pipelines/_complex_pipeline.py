from typing import Any

from rats import apps
from rats import processors as rp
from rats.processors import typing as rpt

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
    def train_and_test_pipeline(self) -> rpt.UPipeline:
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

    @apps.group(rp.Services.GROUPS.EXECUTABLE_PIPELINES)
    def executable_pipelines(self) -> Any:
        return (
            {
                "name": "examples.complex_pipeline",
                "doc": f"""
Example of a pipeline incorporating pipelines defined elsewhere.

Defined in `{__file__}`
""",
                "service_id": apps.autoid(self.train_and_test_pipeline),
            },
        )


class ExampleComplexPipelineServices:
    TRAIN_AND_TEST_PIPELINE = apps.autoid(ExampleComplexPipelineBuilder.train_and_test_pipeline)
