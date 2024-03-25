import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any, NamedTuple, ParamSpec, overload

from oneml.processors import Pipeline
from oneml.processors.dag import IProcess
from oneml.processors.dag._viz import pipeline_to_dot
from oneml.processors.ux import CombinedPipeline, UPipeline, UTask
from oneml.services import IExecutable, ServiceId, T_ServiceType

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
    def get_pipeline(self, name: str) -> UPipeline: ...

    @overload
    def get_pipeline(self, service_id: ServiceId[UPipeline]) -> UPipeline: ...

    def get_pipeline(self, arg: Any) -> Any:
        if isinstance(arg, str):
            return self._app.get_service(ServiceId[UPipeline](arg))
        else:
            return self._app.get_service(arg)


class Example3PipelineContainer(PipelineContainer):
    _app: ServiceContainer

    def __init__(self, app: ServiceContainer) -> None:
        self._app = app

    @task()
    def load_data(self, url: str) -> LoadDataOutput:
        return LoadDataOutput(data=f"Data from {url}")

    @task()
    # @config("model_type", "num_layers")
    def train_model(self, model_type: str, num_layers: int, data: str) -> None:
        # pipeline_context = PipelineContext("p2.1")
        # config_provider = self._app.get_service(ServiceId[ContextProvider[ModelTrainingConfig]](
        #     f"config[train_model][{pipeline_context.task}]",
        # ))
        # config = config_provider()
        print(f"Training model with data: {data} with config {model_type}, {num_layers}")

    @service_provider(ServiceId[UPipeline]("combined-pipeline"))
    def combined_pipeline(self) -> UPipeline:
        p1 = self._get_pipeline("load_data")
        p2 = self._get_pipeline("train_model")
        return CombinedPipeline([p1, p2], dependencies=[p1 >> p2], name="combined_pipeline")

    @service_provider(ServiceId[IExecutable]("draw-pipeline"))
    def run_thing(self) -> IExecutable:
        def run() -> None:
            name = sys.argv[1]
            pipeline = self._app.get_service(ServiceId[UPipeline](name))
            dot = pipeline_to_dot(pipeline)
            dot_str = dot.to_string()
            out_path = Path("../.tmp") / "example.dot"
            out_path.write_text(dot_str)
            print(f"Saved pipeline image to {out_path}")
            print(
                "You can view it in vs-code by installing a graphviz extension e.g. "
                "https://marketplace.visualstudio.com/items?itemName=joaompinto.vscode-graphviz"
            )

        return App(run)

    def _get_pipeline(self, name: str) -> UPipeline:
        return self._app.get_service(ServiceId[UPipeline](name))

    def _get_pipeline_from_service_id(self, service_id: ServiceId[Any]) -> Pipeline[Any, Any]:
        return self._app.get_service(service_id)
