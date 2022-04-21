import logging
from abc import ABC, abstractmethod
from functools import lru_cache
from typing import Tuple
import numpy as np
from dataclasses import dataclass

from oneml.lorenzo.pipelines import PipelineStep, PipelineDataWriter
from ._matrix import RealsMatrix
from ._vector import RealsVector

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class LogisticRegressionParams:
    weights: Tuple[float, ...]
    bias: float


class LogisticRegressionTrainStepPresenter(ABC):
    @abstractmethod
    def save_params(self, data: LogisticRegressionParams) -> None:
        pass

    @abstractmethod
    def save_probs(self, data: RealsVector) -> None:
        pass


class LogisticRegressionTrainStep(PipelineStep):

    _storage: PipelineDataWriter
    _data: RealsMatrix
    _labels: RealsVector
    # Trainer object arguments
    _batch_size: int
    _learning_rate: float

    def __init__(
            self,
            storage: PipelineDataWriter,
            data: RealsMatrix,
            labels: RealsVector,
            batch_size: int,
            learning_rate: float):
        self._storage = storage
        self._data = data
        self._labels = labels
        self._batch_size = batch_size
        self._learning_rate = learning_rate

    def execute(self) -> None:
        self._storage.save(LogisticRegressionParams, self._fit())
        self._storage.save(RealsVector, self._transform())

    def _transform(self) -> RealsVector:
        # Using the parameters from _train(), apply some transformation to the data in self._data
        lrp = self._fit()
        a = np.array(self._data.data)
        return RealsVector(tuple(a@lrp.weights + lrp.bias))

    @lru_cache()
    def _fit(self) -> LogisticRegressionParams:
        """
        - create a trainer with batch_size + learning_rate
        """
        np.random.seed(0)
        return LogisticRegressionParams(
            weights=tuple(np.random.randn(len(self._data.data[0]))),
            bias=0.5,
        )
