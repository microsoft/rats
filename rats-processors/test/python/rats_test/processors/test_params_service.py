import pickle
from dataclasses import dataclass
from typing import NoReturn, TypedDict

import pytest
from hydra_zen import ZenStore

from rats.app import RatsApp
from rats.processors.config import (
    HydraContext,
    IGetConfigAndServiceId,
    RatsProcessorsConfigContexts,
    RatsProcessorsConfigServices,
)
from rats.processors.dag import DagNode, IProcess
from rats.processors.ux import (
    CombinedPipeline,
    InPort,
    Inputs,
    NoInputs,
    OutPort,
    Outputs,
    Task,
    UPipeline,
)


class LoadDataOut(TypedDict):
    data: float


class AOut(TypedDict):
    Z: float


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


class _LoadDataOutputs(Outputs):
    data: OutPort[float]


class _AInputs(Inputs):
    X: InPort[float]


class _AOutputs(Outputs):
    Z: OutPort[float]


class PipelineProvider:
    _params_for_task: IGetConfigAndServiceId

    def __init__(self, params_for_task: IGetConfigAndServiceId) -> None:
        self._params_for_task = params_for_task

    def __call__(self) -> UPipeline:
        data_cfg = self._params_for_task.get_config("data")
        data = Task[NoInputs, _LoadDataOutputs](LoadData, "data", config=data_cfg)

        a_cfg = self._params_for_task.get_config("a")
        a = Task[_AInputs, _AOutputs](A, "a", config=a_cfg)

        return CombinedPipeline(
            pipelines=[data, a], name="test", dependencies=[a.inputs.X << data.outputs.data]
        )


@dataclass
class ExampleObjConf:
    _target_: str = "rats_test.processors.test_params_service.ExampleObj"


@dataclass
class AConf:
    name: str = "a"
    num: int = 1
    example: ExampleObjConf = ExampleObjConf()  # noqa: RUF009


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
def parameters_for_task_service(app: RatsApp, register_configs: None) -> IGetConfigAndServiceId:
    return app.get_service(RatsProcessorsConfigServices.CONFIG_AND_SERVICEID_GETTER)


@pytest.fixture(scope="module")
def pipeline_provider(parameters_for_task_service: IGetConfigAndServiceId) -> PipelineProvider:
    return PipelineProvider(parameters_for_task_service)


def get_hydra_context(data_num: int) -> HydraContext:
    overrides = (
        "+test@configs.a=a_conf",
        "+test@configs.data=data_conf",
        "configs.data.num=" + str(data_num),
    )
    return HydraContext(overrides=overrides)


def get_pipeline(app: RatsApp, pipeline_provider: PipelineProvider, data_num: int) -> UPipeline:
    context = get_hydra_context(data_num)
    with app.open_context(RatsProcessorsConfigContexts.HYDRA, context):
        pipeline = pipeline_provider()
    return pipeline


def verify_pipeline(pipeline: UPipeline, data_num: int) -> None:
    ex = {"name": "a", "num": 1, "example": ExampleObj()}
    assert dict(pipeline._dag.nodes[DagNode("a", "test")].config) == ex
    assert dict(pipeline._dag.nodes[DagNode("data", "test")].config) == {
        "name": "data",
        "num": data_num,
    }


def test_pipeline_config_service(app: RatsApp, pipeline_provider: PipelineProvider) -> None:
    pipeline = get_pipeline(app, pipeline_provider, 5)
    verify_pipeline(pipeline, 5)
    pipeline = get_pipeline(app, pipeline_provider, 10)
    verify_pipeline(pipeline, 10)


def test_serialization(app: RatsApp, pipeline_provider: PipelineProvider) -> None:
    pipeline = get_pipeline(app, pipeline_provider, 5)
    s = pickle.dumps(pipeline)
    lpipeline: UPipeline = pickle.loads(s)
    verify_pipeline(lpipeline, 5)

    with pytest.raises(RuntimeError):
        pickle.dumps(pipeline._dag.nodes[DagNode("a", "test")].config["example"])
