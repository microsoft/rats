import random
import string
from abc import ABC, abstractmethod
from typing import Tuple

from dataclasses import dataclass

from oneml.lorenzo.pipelines import PipelineStep, PipelineDataWriter
from ._sample import ExampleSamplesCollection, ExampleSample


@dataclass(frozen=True)
class FakeSamplesStepConfig:
    num_samples: int


"""
- Need to be able to say "these two pipelines are the same"
    - Want to be able to re-run a pipeline with the same hyperparameters
    - But different data
- Ravi wants the ability to know the input/output of a pipeline without running the pipeline
"""


class IDescribeOutputs(ABC):
    @abstractmethod
    def tell_me_about_the_work(self) -> None:
        """
        Some method to tell us the schema or signature of the step
        """
        pass


class FakeSamplesStep(PipelineStep):
    _storage: PipelineDataWriter
    _num_samples: int

    def __init__(self, storage: PipelineDataWriter, num_samples: int):
        self._storage = storage
        self._num_samples = num_samples

    def configure_data(self) -> None:
        """
        self._storage.add_output(ExampleSamplesCollection)
        """

    def execute(self) -> None:
        samples = self._generate_fake_samples()
        if "some condition":
            self._storage.save(ExampleSamplesCollection, samples)

    def _generate_fake_samples(self) -> ExampleSamplesCollection:
        results = []
        for x in range(self._num_samples):
            results.append(self._generate_fake_sample())
        return ExampleSamplesCollection(samples=tuple(results))

    def _generate_fake_sample(self) -> ExampleSample:
        choices = string.ascii_uppercase
        rand = ''.join(random.choice(choices) for _ in range(10))
        return ExampleSample(name=rand)


class AnotherFakeSamplesStep:

    _storage: PipelineDataWriter

    def __init__(self, storage: PipelineDataWriter):
        self._storage = storage

    def execute(self, num_samples: int) -> ExampleSamplesCollection:
        task = FakeSamplesStep(storage=self._storage, num_samples=num_samples).execute()


class StandardizationTrainStep(PipelineStep):

    # Input
    _data: Tuple[Tuple[float, ...], ...]

    # Output
    _std: Tuple[float, ...]
    _mean: Tuple[float, ...]
    _fitted_data: Tuple[Tuple[float, ...], ...]

    def execute(self) -> None:
        pass


class FittedData:
    pass


class LorenzosStandardizationPredictStep(PipelineStep):

    # Input
    _data: Tuple[Tuple[float, ...], ...]
    _std: Tuple[float, ...]
    _mean: Tuple[float, ...]

    # Output
    _fitted_data: Tuple[Tuple[float, ...], ...]

    _storage: PipelineDataWriter

    def __init__(
            self,
            storage: PipelineDataWriter,
            data: Tuple[Tuple[float, ...], ...],
            std: Tuple[float, ...],
            mean: Tuple[float, ...]):
        self._storage = storage
        self._data = data
        self._std = std
        self._mean = mean

    def execute(self) -> None:
        self._storage.save(FittedData, self._get_fitted_data())

    def _get_fitted_data(self) -> Tuple[Tuple[float, ...], ...]:
        return JaviersStandardizationPredictStep(self._std, self._mean).execute(self._data)


class RavisStandardizationPredictStep(PipelineStep):

    # Input
    _data: Tuple[Tuple[float, ...], ...]
    _std: Tuple[float, ...]
    _mean: Tuple[float, ...]

    # Output
    _fitted_data: Tuple[Tuple[float, ...], ...]

    def execute(self) -> None:
        self._fitted_data = JaviersStandardizationPredictStep(self._std, self._mean).execute(self._data)


class JaviersStandardizationPredictStep:

    _std: Tuple[float, ...]
    _mean: Tuple[float, ...]

    def __init__(
            self,
            std: Tuple[float, ...],
            mean: Tuple[float, ...]):
        self._std = std
        self._mean = mean

    def execute(self, _data: Tuple[Tuple[float, ...], ...]) -> Tuple[Tuple[float, ...], ...]:
        pass


class StandardizationGraph:
    pass
