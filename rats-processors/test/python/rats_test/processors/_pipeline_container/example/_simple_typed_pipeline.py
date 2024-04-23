import copy
from typing import NamedTuple, cast

from rats import apps
from rats import processors as rp
from rats.processors import ux


class SubModel:
    def __init__(self, gamma: float):
        self.gamma = gamma

    def __str__(self) -> str:
        return f"SubModel(gamma={self.gamma})"


class Model:
    trained: bool

    def __init__(
        self,
        model_name: str,
        num_layers: int,
        sub_model: SubModel,
    ):
        self.model_name = model_name
        self.num_layers = num_layers
        self.sub_model = sub_model
        self.trained = False

    def train(self) -> None:
        self.trained = True

    def __str__(self) -> str:
        status = "trained" if self.trained else "untrained"
        return f"Model(model_name={self.model_name}, num_layers={self.num_layers}, sub_model={self.sub_model}, status={status})"


class LoadDataInputs(ux.Inputs):
    url: ux.InPort[str]


class LoadDataOutputs(ux.Outputs):
    data: ux.OutPort[str]


class LoadDataOutput(NamedTuple):
    data: str


class TrainModelInputs(ux.Inputs):
    model: ux.InPort[Model]
    epochs: ux.InPort[int]
    data: ux.InPort[str]


class TrainModelOutputs(ux.Outputs):
    message: ux.OutPort[str]
    length: ux.OutPort[int]


class TrainModelOutput(NamedTuple):
    message: str
    model: Model


TestModelInputs = TrainModelInputs


class TestModelOutputs(ux.Outputs):
    message: ux.OutPort[str]


class TestModelOutput(NamedTuple):
    message: str


class TrainPipelineInputs(ux.Inputs):
    url: ux.InPort[str]
    model: ux.InPort[Model]
    epochs: ux.InPort[int]


class TrainPipelineOutputs(ux.Outputs):
    message: ux.OutPort[str]
    model: ux.OutPort[Model]


TrainPipeline = ux.Pipeline[TrainPipelineInputs, TrainPipelineOutputs]


class TestPipelineInputs(ux.Inputs):
    url: ux.InPort[str]
    model: ux.InPort[Model]


class TestPipelineOutputs(ux.Outputs):
    message: ux.OutPort[str]


TestPipeline = ux.Pipeline[TestPipelineInputs, TestPipelineOutputs]


class ExampleSimpleTypedPipelineBuilder(rp.PipelineContainer):
    @rp.task[LoadDataInputs, LoadDataOutputs]
    def load_data(self, url: str) -> LoadDataOutput:
        return LoadDataOutput(data=f"Data from {url}")

    @rp.task[TrainModelInputs, TrainModelOutputs]
    def train_model(self, model: Model, data: str, epochs: int = 10) -> TrainModelOutput:
        message = f"Training model\n\tdata: {data}\n\tepochs: {epochs}\n\tmodel: {model}"
        model = copy.deepcopy(model)
        model.train()
        return TrainModelOutput(message=message, model=model)

    @rp.task[TestModelInputs, TestModelOutputs]
    def test_model(self, model: Model, data: str) -> TestModelOutput:
        message = f"Testing model\n\tdata: {data}\n\tmodel: {model}"
        return TestModelOutput(message=message)

    @rp.pipeline
    def train_pipeline(self) -> TrainPipeline:
        load = self.load_data()
        train = self.get(apps.method_service_id(self.train_model))
        p = self.combine([load, train], dependencies=[load.outputs.data >> train.inputs.data])
        return cast(TrainPipeline, p)

    @rp.pipeline
    def test_pipeline(self) -> TestPipeline:
        load = self.load_data()
        test = self.get(apps.method_service_id(self.test_model))
        p = self.combine([load, test], dependencies=[load.outputs.data >> test.inputs.data])
        return cast(TestPipeline, p)


class ExampleSimpleTypedPipelineServices:
    TRAIN_PIPELINE = apps.method_service_id(ExampleSimpleTypedPipelineBuilder.train_pipeline)
    TEST_PIPELINE = apps.method_service_id(ExampleSimpleTypedPipelineBuilder.test_pipeline)
    LOAD_DATA = apps.method_service_id(ExampleSimpleTypedPipelineBuilder.load_data)
    TRAIN_MODEL = apps.method_service_id(ExampleSimpleTypedPipelineBuilder.train_model)
