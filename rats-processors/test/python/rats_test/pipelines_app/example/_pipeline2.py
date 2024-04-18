from typing import NamedTuple, cast

from rats import apps
from rats import pipelines_app as rpa
from rats.processors import ux


class LoadDataInputs(ux.Inputs):
    url: ux.InPort[str]


class LoadDataOutputs(ux.Outputs):
    data: ux.OutPort[str]


class LoadDataOutput(NamedTuple):
    data: str


class TrainModelInputs(ux.Inputs):
    model_type: ux.InPort[str]
    num_layers: ux.InPort[int]
    data: ux.InPort[str]


class TrainModelOutputs(ux.Outputs):
    message: ux.OutPort[str]
    length: ux.OutPort[int]


class TrainModelOutput(NamedTuple):
    message: str
    length: int


class P2Inputs(ux.Inputs):
    url: ux.InPort[str]
    model_type: ux.InPort[str]
    num_layers: ux.InPort[int]


class P2Outputs(ux.Outputs):
    message: ux.OutPort[str]
    length: ux.OutPort[int]


class ExamplePipelineContainer2(rpa.PipelineContainer):
    @rpa.task[LoadDataInputs, LoadDataOutputs]
    def load_data(self, url: str) -> LoadDataOutput:
        return LoadDataOutput(data=f"Data from {url}")

    @rpa.task[TrainModelInputs, TrainModelOutputs]
    def train_model(self, model_type: str, num_layers: int, data: str) -> TrainModelOutput:
        message = f"Training model with data: {data} with config {model_type}, {num_layers}"
        return TrainModelOutput(message=message, length=len(message))

    @rpa.pipeline
    def p2(self) -> ux.Pipeline[P2Inputs, P2Outputs]:
        p1 = self.load_data()
        p2 = self.get(apps.method_service_id(self.train_model))
        p = self.combine([p1, p2], dependencies=[p1.outputs.data >> p2.inputs.data])
        return cast(ux.Pipeline[P2Inputs, P2Outputs], p)
