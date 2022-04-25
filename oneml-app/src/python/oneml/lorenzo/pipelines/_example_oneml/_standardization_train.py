from functools import lru_cache
from typing import Tuple
import numpy as np

from dataclasses import dataclass

from oneml.lorenzo.pipelines import PipelineStep, PipelineDataWriter
from ._matrix import RealsMatrix


@dataclass(frozen=True)
class StandardizationParams:
    scale: Tuple[float, ...]
    mean: Tuple[float, ...]


class StandardizationTrainStep(PipelineStep):
    """
    comments:
    -
    """

    _storage: PipelineDataWriter
    _matrix: RealsMatrix

    def __init__(self, storage: PipelineDataWriter, matrix: RealsMatrix):
        self._storage = storage
        self._matrix = matrix

    def execute(self) -> None:
        self._storage.save(StandardizationParams, self._fit())
        self._storage.save(RealsMatrix, self._transform())

    def _transform(self) -> RealsMatrix:
        # Using the parameters from _train(), apply some transformation to the data in self._data
        sp = self._fit()
        standardized = (np.array(self._matrix.data) - sp.mean) / sp.scale
        m = (
            tuple(row)
            for row in standardized
        )
        return RealsMatrix(tuple(m))

    @lru_cache()
    def _fit(self) -> StandardizationParams:
        a = np.array(self._matrix.data)
        mean = a.mean(axis=0)
        scale = a.std(axis=0)
        return StandardizationParams(mean=mean, scale=scale)
