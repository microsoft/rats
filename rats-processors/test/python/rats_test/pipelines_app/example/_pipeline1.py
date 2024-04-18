from typing import NamedTuple

from rats import apps
from rats import pipelines_app as rpa
from rats.processors import ux


class LoadDataOutput(NamedTuple):
    data: str


class TrainModelOutput(NamedTuple):
    message: str
    length: int


class ExamplePipelineContainer(rpa.PipelineContainer):
    @rpa.task
    def load_data(self, url: str) -> LoadDataOutput:
        return LoadDataOutput(data=f"Data from {url}")

    @rpa.task
    def train_model(self, model_type: str, num_layers: int, data: str) -> TrainModelOutput:
        message = f"Training model with data: {data} with config {model_type}, {num_layers}"
        return TrainModelOutput(message=message, length=len(message))

    @rpa.pipeline
    def p1(self) -> ux.UPipeline:
        p1 = self.load_data()
        p2 = self.get(apps.method_service_id(self.train_model))
        p = self.combine([p1, p2], dependencies=[p1 >> p2])
        return p


class ExamplePipelineServices:
    P1 = apps.method_service_id(ExamplePipelineContainer.p1)
