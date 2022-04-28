"""Hyperparameter Optimization."""

from abc import ABC, abstractmethod
from collections import UserDict
from dataclasses import dataclass
from functools import partial
from typing import Any, Callable, Dict, List

import optuna

from ...oneml.lorenzo.pipelines import PipelineStep


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

    _num_trials: int
    _search_space: SearchSpace
    _algorithm: Algorithm
    _objective: Objective

    def __init__(
        self,
        num_trials: int,
        search_space: Dict[str, Distribution],
        algorithm: str,
        objective: Objective,
    ) -> None:
        super().__init__()
        self._num_trials = num_trials
        self._search_space = search_space
        self._algorithm = algorithm
        self._objective = objective

    @abstractmethod
    def execute(self) -> None:
        pass

    @property
    def num_trials(self) -> int:
        return self._num_trials


class OptunaStep(HPOStep):
    def execute(self) -> None:
        study = optuna.create_study()
        study.optimize(self._trial_objective, n_trials=self.num_trials)

    def _trial_objective(self, trial: optuna.Trial) -> int:
        trial_cfg = self._draw_from_search_space(trial)
        self._objective(trial_cfg)
        return 0.0  # return self._objective.pipeline.storage

    def _draw_from_search_space(self, trial: optuna.Trial) -> Dict[str, Any]:
        draw = {}
        for name, dist in self._search_space.items():
            draw[name] = self._suggest(trial, name)(name, dist)
        return draw

    def _suggest(trial: optuna.Trial, name: str) -> Callable[..., Any]:
        return {
            "categorical": trial.suggest_categorical,
            "float": trial.suggest_float,
            "int": trial.suggest_int,
        }[name]


class KatibStep(HPOStep):
    pass


class HyperoptStep(HPOStep):
    pass


class RayTuneStep(HPOStep):
    pass
