import copy
from typing import Any, NamedTuple, cast

from rats import apps
from rats import processors as rp
from rats.processors import typing as rpt


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


class LoadDataInputs(rpt.Inputs):
    url: rpt.InPort[str]


class LoadDataOutputs(rpt.Outputs):
    data: rpt.OutPort[str]


class LoadDataOutput(NamedTuple):
    data: str


class TrainModelInputs(rpt.Inputs):
    model: rpt.InPort[Model]
    epochs: rpt.InPort[int]
    data: rpt.InPort[str]


class TrainModelOutputs(rpt.Outputs):
    message: rpt.OutPort[str]
    length: rpt.OutPort[int]


class TrainModelOutput(NamedTuple):
    message: str
    model: Model


TestModelInputs = TrainModelInputs


class TestModelOutputs(rpt.Outputs):
    message: rpt.OutPort[str]


class TestModelOutput(NamedTuple):
    message: str


class TrainPipelineInputs(rpt.Inputs):
    url: rpt.InPort[str]
    model: rpt.InPort[Model]
    epochs: rpt.InPort[int]


class TrainPipelineOutputs(rpt.Outputs):
    message: rpt.OutPort[str]
    model: rpt.OutPort[Model]


TrainPipeline = rpt.Pipeline[TrainPipelineInputs, TrainPipelineOutputs]


class TestPipelineInputs(rpt.Inputs):
    url: rpt.InPort[str]
    model: rpt.InPort[Model]


class TestPipelineOutputs(rpt.Outputs):
    message: rpt.OutPort[str]


TestPipeline = rpt.Pipeline[TestPipelineInputs, TestPipelineOutputs]


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
        train = self.get(apps.autoid(self.train_model))
        p = self.combine([load, train], dependencies=[load.outputs.data >> train.inputs.data])
        return cast(TrainPipeline, p)

    @rp.pipeline
    def test_pipeline(self) -> TestPipeline:
        load = self.load_data()
        test = self.get(apps.autoid(self.test_model))
        p = self.combine([load, test], dependencies=[load.outputs.data >> test.inputs.data])
        return cast(TestPipeline, p)

    @apps.group(rp.Services.GROUPS.EXECUTABLE_PIPELINES)
    def executable_pipelines(self) -> Any:
        return (
            {
                "name": "examples.typed_simple_pipeline",
                "doc": f"""
Example typed simple pipeline.

Defined in `{__file__}`
""",
                "service_id": apps.autoid(self.train_pipeline),
            },
        )


class ExampleSimpleTypedPipelineServices:
    TRAIN_PIPELINE = apps.autoid(ExampleSimpleTypedPipelineBuilder.train_pipeline)
    TEST_PIPELINE = apps.autoid(ExampleSimpleTypedPipelineBuilder.test_pipeline)
    LOAD_DATA = apps.autoid(ExampleSimpleTypedPipelineBuilder.load_data)
    TRAIN_MODEL = apps.autoid(ExampleSimpleTypedPipelineBuilder.train_model)
