from collections.abc import Callable
from typing import Any, Generic, NamedTuple, ParamSpec, Protocol, TypeVar, overload

from oneml.processors import Pipeline
from oneml.processors.dag import IProcess
from oneml.processors.ux import CombinedPipeline, UPipeline, UTask
from oneml.services import (
    ContextId,
    ContextProvider,
    IExecutable,
    ServiceId,
    T_ContextType,
    T_ServiceType,
)

from ..pipelines.dag import PipelineNode
from ._v2 import App, ServiceContainer, service_provider


class LoadDataOutput(NamedTuple):
    data: str


class P1(IProcess):
    def process(self, url: str) -> LoadDataOutput:
        return LoadDataOutput(data=f"Data from {url}")


class P2(IProcess):
    def process(self, data: str) -> None:
        print(f"Training model with data: {data}")


P = ParamSpec("P")


def task() -> Callable[[Callable[P, T_ServiceType]], Callable[[ServiceContainer], UPipeline]]:
    def wrapper(fn: Callable[P, T_ServiceType]) -> Callable[[ServiceContainer], UPipeline]:
        service_id = ServiceId[UPipeline](fn.__name__)

        class _P(IProcess):
            process = fn

        _P.__name__ = fn.__name__

        return service_provider(service_id)(lambda _: UTask(_P))

    return wrapper


class ModelTrainingConfig(NamedTuple):
    model: str


class PipelineContext(NamedTuple):
    task: str


class PipelineContainer(ServiceContainer):
    def __init__(self, app: ServiceContainer) -> None:
        self._app = app

    @overload
    def get_pipeline(self, name: str) -> UPipeline:
        ...

    @overload
    def get_pipeline(self, service_id: ServiceId[UPipeline]) -> UPipeline:
        ...

    def get_pipeline(self, arg: Any) -> Any:
        if isinstance(arg, str):
            return self._app.get_service(ServiceId[UPipeline](arg))
        else:
            return self._app.get_service(arg)


class LoadDataInput(NamedTuple):
    url: str


class ContextPublisher(Generic[T_ContextType], Protocol):
    def __call__(self, data: T_ContextType) -> None:
        pass


class DataLoader(IExecutable):
    _url: ContextProvider[str]
    _output: ContextPublisher[LoadDataOutput]

    def __init__(
        self, url: ContextProvider[str], output: ContextPublisher[LoadDataOutput]
    ) -> None:
        self._url = url
        self._output = output

    def execute(self) -> None:
        self._output(LoadDataOutput(data=f"Data from {self._url()}"))


class TrainModel(IExecutable):
    _data: ContextProvider[LoadDataOutput]
    _learning_rate: ContextProvider[float]

    def __init__(
        self,
        data: ContextProvider[LoadDataOutput],
        learning_rate: ContextProvider[float],
    ) -> None:
        self._data = data
        self._learning_rate = learning_rate

    def execute(self) -> None:
        print(f"Training model with data: {self._data()} {self._learning_rate()}")


def chain(*args: IExecutable) -> IExecutable:
    def run() -> None:
        for app in args:
            app.execute()

    return App(run)


class SimpleData:
    _data: dict[ContextId[Any], Any]

    def __init__(self):
        self._data = {}

    def get(self, key: ContextId[T_ContextType]) -> T_ContextType:
        return self._data[key]

    def set(self, key: ContextId[T_ContextType], value: T_ContextType) -> None:
        self._data[key] = value


class DagClient:
    def get_input_node(self, node: PipelineNode) -> PipelineNode:
        ...


T_InputType = TypeVar("T_InputType")
T_OutputType = TypeVar("T_OutputType")


class PNode(NamedTuple, Generic[T_InputType, T_OutputType]):
    name: str


class NPort(NamedTuple, Generic[T_OutputType]):
    name: str


class TrainModelInput(NamedTuple):
    data: NPort[dict[Any, Any]]
    learning_rate: NPort[float]


class ExamplePipelineNodes:
    LOAD_DATA = PNode[str, dict[Any, Any]]("load-data")
    TRAIN_MODEL = PNode[TrainModelInput, None]("train-model")


def edge(out_port: NPort[T], in_port: NPort[T]) -> None:
    pass


class Example3PipelineContainer(ServiceContainer):
    _app: ServiceContainer

    def __init__(self, app: ServiceContainer) -> None:
        self._app = app

    def my_dag(self) -> Pipeline:
        p1 = ExamplePipelineNodes.LOAD_DATA
        p2 = ExamplePipelineNodes.TRAIN_MODEL
        return CombinedPipeline(
            [p1, p2],
            dependencies=[p1 >> p2],
            name="combined_pipeline",
        )

    def my_pipeline(self) -> IExecutable:
        return chain(
            self._app.get_service(ServiceId[IExecutable]("load-data")),
            self._app.get_service(ServiceId[IExecutable]("train-model")),
        )

    @service_provider(ServiceId[IExecutable]("load-data"))
    def load_data(self) -> DataLoader:
        data_client = self._app.get_service(ServiceId[SimpleData]("pipeline-data"))
        node = self._app.get_service(ServiceId[SimpleData]("pipeline-node-context"))
        return DataLoader(
            url=lambda: "http://example.com",
            output=lambda data: data_client.set(ContextId[LoadDataOutput]("load-data"), data),
        )

    @service_provider(ServiceId[IExecutable]("train-model"))
    def train_model(self) -> TrainModel:
        data_client = self._app.get_service(ServiceId[SimpleData]("pipeline-data"))
        dag_client = self._app.get_service(ServiceId[DagClient]("dag-client"))

        node = self._app.get_service(ServiceId[ContextProvider[PipelineNode]]("pipeline-node"))
        source_node = dag_client.get_input_node(node())

        return TrainModel(
            data=lambda: data_client.get(ContextId[LoadDataOutput](f"/{source_node()}[data]")),
            learning_rate=lambda: data_client.get(ContextId[LoadDataOutput](source_node())),
        )

    @service_provider(ServiceId[SimpleData]("pipeline-data"))
    def data(self) -> SimpleData:
        return SimpleData()

    @service_provider(ServiceId[SimpleData]("pipeline-node-context"))
    def node_ctx(self) -> ContextProvider[PipelineNode]:
        return lambda: PipelineNode("load-data.1")

    @service_provider(ServiceId[DagClient]("dag-client"))
    def dag_client(self) -> DagClient:
        return DagClient()
