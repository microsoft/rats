import pickle
from dataclasses import dataclass
from typing import Iterator, NoReturn, Sequence, TypedDict

import pytest
from hydra_zen import ZenStore

from oneml.app import OnemlApp
from oneml.processors.dag import DagNode, IProcess
from oneml.processors.services import (
    HydraContext,
    OnemlProcessorsContexts,
    OnemlProcessorsServices,
    ParametersForTaskService,
)
from oneml.processors.ux import CombinedPipeline, Pipeline, Task

LoadDataOut = TypedDict("LoadDataOut", {"data": float})
AOut = TypedDict("AOut", {"Z": float})


class LoadData(IProcess):
    def __init__(self, name: str, num: float) -> None:
        self.name = name
        self.num = num

    def process(self) -> LoadDataOut:
        return {"data": self.num}


class ExampleObj:
    def __eq__(self, o: object) -> bool:
        return isinstance(o, ExampleObj)

    def __getstate__(self) -> NoReturn:
        raise RuntimeError("Non serializable example object.")


class A(IProcess):
    def __init__(self, name: str, num: int, example: ExampleObj) -> None:
        self.name = name
        self.num = num
        self.example = example

    def process(self, X: float) -> AOut:
        return {"Z": X + self.num}


class PipelineProvider:
    _params_for_task: ParametersForTaskService

    def __init__(self, params_for_task: ParametersForTaskService) -> None:
        self._params_for_task = params_for_task

    def __call__(self) -> Pipeline:
        data_cfg = self._params_for_task.get_config("data")
        data = Task(LoadData, "data", config=data_cfg)

        a_cfg = self._params_for_task.get_config("a")
        a = Task(A, "a", config=a_cfg)

        return CombinedPipeline(
            pipelines=[data, a], name="test", dependencies=[a.inputs.X << data.outputs.data]
        )


@dataclass
class ExampleObjConf:
    _target_: str = "oneml_test.processors.test_params_service.ExampleObj"


@dataclass
class AConf:
    name: str = "a"
    num: int = 1
    example: ExampleObjConf = ExampleObjConf()


@dataclass
class DataConf:
    name: str = "data"
    num: int = 5


@pytest.fixture(scope="module")
def register_configs() -> None:
    test_store = ZenStore(name="test-store")
    test_store(AConf(), name="a_conf", group="test")
    test_store(DataConf(), name="data_conf", group="test")
    test_store.add_to_hydra_store()


@pytest.fixture(scope="module")
def parameters_for_task_service(app: OnemlApp, register_configs: None) -> ParametersForTaskService:
    return app.get_service(OnemlProcessorsServices.PARAMETERS_FOR_TASK_SERVICE)


@pytest.fixture(scope="module")
def pipeline_provider(parameters_for_task_service: ParametersForTaskService) -> PipelineProvider:
    return PipelineProvider(parameters_for_task_service)


def get_hydra_context(data_num: int) -> HydraContext:
    overrides = (
        "+test@task_parameters.a.config=a_conf",
        "+test@task_parameters.data.config=data_conf",
        "task_parameters.data.config.num=" + str(data_num),
    )
    return HydraContext(overrides=overrides)


def get_pipeline(app: OnemlApp, pipeline_provider: PipelineProvider, data_num: int) -> Pipeline:
    context = get_hydra_context(data_num)
    with app.open_context(OnemlProcessorsContexts.HYDRA, context):
        pipeline = pipeline_provider()
    return pipeline


def verify_pipeline(pipeline: Pipeline, data_num: int) -> None:
    ex = {"name": "a", "num": 1, "example": ExampleObj()}
    assert dict(pipeline._dag.nodes[DagNode("a", "test")].config) == ex
    assert dict(pipeline._dag.nodes[DagNode("data", "test")].config) == {
        "name": "data",
        "num": data_num,
    }


def test_pipeline_config_service(app: OnemlApp, pipeline_provider: PipelineProvider) -> None:
    pipeline = get_pipeline(app, pipeline_provider, 5)
    verify_pipeline(pipeline, 5)
    pipeline = get_pipeline(app, pipeline_provider, 10)
    verify_pipeline(pipeline, 10)


def test_serialization(app: OnemlApp, pipeline_provider: PipelineProvider) -> None:
    pipeline = get_pipeline(app, pipeline_provider, 5)
    s = pickle.dumps(pipeline)
    pipeline = pickle.loads(s)
    verify_pipeline(pipeline, 5)

    with pytest.raises(RuntimeError):
        pickle.dumps(pipeline._dag.nodes[DagNode("a", "test")].config["example"])
