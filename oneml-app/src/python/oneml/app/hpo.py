"""Hyperparameter Optimization."""

from abc import ABC, abstractmethod
from collections import UserDict
from dataclasses import dataclass
from typing import Any, Dict, List

from ..lorenzo.pipelines import PipelineStep, PipelineStorage


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


class Objective:
    pipeline: PipelineStep
    metric: List[str]


class HPOStep(PipelineStep, ABC):
    def __init__(
        self,
        num_trials: int,
        search_space: Dict[str, Distribution],
        algorithm: str,
        objective: PipelineStorage,
    ) -> None:
        super().__init__()
        self.num_trials = num_trials
        self.search_space = search_space
        self.algorithm = algorithm
        self.objective = objective

    @abstractmethod
    def execute(self) -> None:
        pass
