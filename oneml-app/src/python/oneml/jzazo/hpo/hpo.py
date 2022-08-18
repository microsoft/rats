# type: ignore
# flake8: noqa
"""Hyperparameter Optimization."""

from abc import ABC, abstractmethod
from collections import UserDict
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Union

import optuna

from oneml.lorenzo.pipelines import (
    NamespacedStorage,
    PipelineStep,
    PipelineStorage,
    TypeNamespaceClient,
)


@dataclass
class Distribution:
    type: str


@dataclass
class CategoricalDistribution(Distribution):
    type: str = "categorical"
    params: Dict[str, Any] = field(default_factory=dict)


class SearchSpace(UserDict):
    pass


@dataclass
class Objective:
    pipeline_factory: Any
    metric: List[str]
    storage: PipelineStorage
    namespace_client: TypeNamespaceClient

    def __call__(self, config: Dict[str, Any], id: Union[str, int]) -> Any:
        params_namespace = self.namespace_client.get_namespace(f"hyperparams-{id}")
        params_storage = NamespacedStorage(storage=self.storage, namespace=params_namespace)
        params_storage.save(SearchSpace, config)
        pipeline = self.pipeline_factory(storage=params_storage, **config)
        pipeline.execute()


class HPOStep(PipelineStep, ABC):

    _num_trials: int
    _search_space: SearchSpace
    _algorithm: Any
    _objective: Objective
    _storage: PipelineStorage

    def __init__(
        self,
        num_trials: int,
        search_space: SearchSpace,
        algorithm: Any,
        objective: Objective,
        storage: PipelineStorage,
    ) -> None:
        super().__init__()
        self._num_trials = num_trials
        self._search_space = search_space
        self._algorithm = algorithm
        self._objective = objective
        self._storage = storage

    @abstractmethod
    def execute(self) -> None:
        pass

    @property
    def num_trials(self) -> int:
        return self._num_trials


class OptunaStep(HPOStep):
    def execute(self) -> None:
        study = optuna.create_study(sampler=self._algorithm)
        study.optimize(self._trial_objective, n_trials=self.num_trials)

    def _trial_objective(self, trial: optuna.Trial) -> float:
        trial_cfg = self._draw_from_search_space(trial)
        self._objective(trial_cfg, trial.number)
        return 0.0  # return self._objective.pipeline.storage

    def _draw_from_search_space(self, trial: optuna.Trial) -> Dict[str, Any]:
        draw = {}
        for name, dist in self._search_space.items():
            draw[name] = self._suggest(trial, dist)(name, **dist.params)
        return draw

    def _suggest(self, trial: optuna.Trial, dist: Distribution) -> Callable[..., Any]:
        return {
            "categorical": trial.suggest_categorical,
            "float": trial.suggest_float,
            "int": trial.suggest_int,
        }[dist.type]


class KatibStep(HPOStep):
    pass


class HyperoptStep(HPOStep):
    pass


class RayTuneStep(HPOStep):
    pass
