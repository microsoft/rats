from abc import ABC, abstractmethod
from functools import partial
from typing import Any, Callable, List, Tuple, Type

from oneml.lorenzo.pipelines import InMemoryStorage, PipelineStep, TypeNamespaceClient
from oneml.lorenzo.pipelines._example_oneml._hyperparameter_search import HyperparameterSearchStep
from oneml.lorenzo.pipelines._example_oneml._input_data import InputDataStep, InputLabelsStep
from oneml.lorenzo.pipelines._example_oneml._logistic_regression_train import (
    LogisticRegressionTrainStep,
)
from oneml.lorenzo.pipelines._example_oneml._matrix import RealsMatrix
from oneml.lorenzo.pipelines._example_oneml._pipeline import StandardizedLogisticRegressionPipeline
from oneml.lorenzo.pipelines._example_oneml._search_space import TrainerParameterSearchSpace
from oneml.lorenzo.pipelines._example_oneml._standardization_train import StandardizationTrainStep
from oneml.lorenzo.pipelines._example_oneml._vector import RealsVector


def _get_search_space() -> TrainerParameterSearchSpace:
    batch_sizes = [512, 1024, 2048]
    learning_rates = [
        1e-5, 1e-4, 1e-3,
    ]
    return TrainerParameterSearchSpace(tuple(batch_sizes), tuple(learning_rates))


def _test() -> None:
    storage = InMemoryStorage()
    namespace_client = TypeNamespaceClient()

    pipeline = HyperparameterSearchStep(
        storage=storage,
        namespace_client=namespace_client,
        search_space=_get_search_space(),
        pipeline_factory=partial(StandardizedLogisticRegressionPipeline, namespace_client=namespace_client)
    )
    pipeline.execute()

    for k, v in storage._data.items():
        print(k)


class NamespacedData:

    def __init__(self, step_ref: Type[PipelineStep], data_ref: Type[object]):
        pass


class PipelineConfigPresenter:
    _things: List[Any]

    def __init__(self):
        self._things = []

    def execute(self, step: PipelineStep) -> None:
        self._things.append(f"execute {step}")

    def require(self, data_id: NamespacedData) -> None:
        pass


class PipelineConfigCallback(ABC):
    @abstractmethod
    def __call__(self, presenter: PipelineConfigPresenter) -> None:
        pass


class NewPipelineStep:

    _callables: Tuple[Callable[[PipelineConfigPresenter], None], ...]

    def __init__(self, *callables: Callable[[PipelineConfigPresenter], None]):
        self._callables = tuple(callables)

    def resolve(self, presenter: PipelineConfigPresenter) -> None:
        for callback in self._callables:
            callback(presenter)


class MyPipeline:

    _steps: Tuple[NewPipelineStep, ...]

    def __init__(self, steps: Tuple[NewPipelineStep, ...]):
        self._steps = steps

    def execute(self) -> None:
        for step in self._steps:
            presenter = PipelineConfigPresenter()
            step.resolve(presenter)


def _test2() -> None:
    storage = InMemoryStorage()
    namespace_client = TypeNamespaceClient()

    pipeline = MyPipeline(tuple([
        NewPipelineStep(lambda x: x.execute(InputLabelsStep(storage=storage))),
        NewPipelineStep(lambda x: x.execute(InputDataStep(storage=storage))),
        NewPipelineStep(
            lambda x: x.require(NamespacedData(InputDataStep, RealsMatrix)),
            lambda x: x.execute(StandardizationTrainStep(
                storage=storage,
                matrix=storage.load(RealsMatrix)
            ))
        ),
        NewPipelineStep(
            lambda x: x.require(NamespacedData(InputDataStep, RealsMatrix)),
            lambda x: x.require(NamespacedData(InputLabelsStep, RealsVector)),
            lambda x: x.execute(LogisticRegressionTrainStep(
                storage=storage,
                data=storage.load(RealsMatrix),
                labels=storage.load(RealsVector),
                batch_size=32,
                learning_rate=1e-3,
            ))
        ),
    ]))

    """
    dag = Dag()
    dag.add_step(StepId1, step1)
    dag.add_step(StepId2, step2)
    dag.bind(StepId2, step2)
    
    """

    pipeline.execute()


if __name__ == "__main__":
    _test()
