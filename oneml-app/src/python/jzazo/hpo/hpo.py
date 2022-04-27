"""Hyperparameter Optimization."""

from abc import ABC, abstractmethod
from collections import UserDict
from dataclasses import dataclass
from functools import partial
from typing import Any, Dict, List

from ...oneml.lorenzo.pipelines import PipelineStep, PipelineStorage


@dataclass(frozen=True)
class Distribution:
    name: str
    low: int
    high: int


@dataclass(frozen=True)
class Algorithm:
    name: str
    params: Dict[str, Any]


class SearchSpace(UserDict[str, Distribution]):
    data: Dict[str, Distribution]


@dataclass
class Objective:
    pipeline: partial[PipelineStep]
    metric: List[str]

    def __call__(self, config: Dict[str, Any]) -> Any:
        pipeline = self.pipeline(**config)
        pipeline.execute()


class HPOStep(PipelineStep, ABC):
    def __init__(
        self,
        num_trials: int,
        search_space: Dict[str, Distribution],
        algorithm: str,
        objective: Objective,
    ) -> None:
        super().__init__()
        self.num_trials = num_trials
        self.search_space = search_space
        self.algorithm = algorithm
        self.objective = objective

    @abstractmethod
    def execute(self) -> None:
        pass


class OptunaStep(HPOStep):
    pass


class KatibStep(HPOStep):
    pass


class HyperoptStep(HPOStep):
    pass


class RayTuneStep(HPOStep):
    pass
