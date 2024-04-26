from typing import Any, NamedTuple

from rats import apps
from rats import processors as rp
from rats.processors import typing as rpt


class LoadDataOutput(NamedTuple):
    data: str


class TrainModelOutput(NamedTuple):
    message: str
    length: int


class ExampleSimpleUntypedPipelineBuilder(rp.PipelineContainer):
    @rp.task
    def load_data(self, url: str) -> LoadDataOutput:
        return LoadDataOutput(data=f"Data from {url}")

    @rp.task
    def train_model(self, model_type: str, num_layers: int, data: str) -> TrainModelOutput:
        message = f"Training model with data: {data} with config {model_type}, {num_layers}"
        return TrainModelOutput(message=message, length=len(message))

    @rp.pipeline
    def train_pipeline(self) -> rpt.UPipeline:
        p1 = self.load_data()
        p2 = self.get(apps.autoid(self.train_model))
        p = self.combine([p1, p2], dependencies=[p1 >> p2])
        return p

    @apps.group(rp.Services.GROUPS.EXECUTABLE_PIPELINES)
    def executable_pipelines(self) -> Any:
        return (
            {
                "name": "examples.untyped_simple_pipeline",
                "doc": f"""
Example untyped simple pipeline.  Looks like a training pipeline, but does not really do anything
besides some string manipulation to construct a message.

Defined in `{__file__}`
""",
                "service_id": apps.autoid(self.train_pipeline),
            },
        )


class ExampleSimpleUntypedPipelineServices:
    TRAIN_PIPELINE = apps.autoid(ExampleSimpleUntypedPipelineBuilder.train_pipeline)
