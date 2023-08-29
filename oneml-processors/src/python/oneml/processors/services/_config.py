from abc import abstractmethod
from functools import cache
from pathlib import Path
from typing import Any, Iterator, Mapping, Protocol, Sequence, cast

from hydra_zen import instantiate
from omegaconf import DictConfig

from oneml.services import ServiceId

from ..schemas.configs import PipelineConfig
from ._hydra import PipelineConfigService

CONF_PATH = Path("src/resources/conf")


class ConfigsForTaskService(Protocol):
    @abstractmethod
    def get_config(self, task: str, overrides: Sequence[str] = []) -> Mapping[str, Any] | None:
        ...


class ServiceIdsForTaskService(Protocol):
    @abstractmethod
    def get_service_ids(
        self, task: str, overrides: Sequence[str] = []
    ) -> Mapping[str, ServiceId[Any]] | None:
        ...


class ParametersForTaskService(ConfigsForTaskService, ServiceIdsForTaskService):
    def get_config_and_service_ids(
        self, task: str, overrides: Sequence[str] = []
    ) -> tuple[Mapping[str, Any] | None, Mapping[str, ServiceId[Any]] | None]:
        return self.get_config(task, overrides), self.get_service_ids(task, overrides)


class InstantiateConfMapping(Mapping[str, Any]):
    _cfg: DictConfig

    def __init__(self, cfg: DictConfig) -> None:
        self._cfg = cfg

    @cache
    def _instantiate(self) -> Mapping[str, Any]:
        return instantiate(self._cfg)

    def __getitem__(self, key: str) -> Any:
        return self._instantiate()[key]

    def __hash__(self) -> int:
        return hash(self._cfg)

    def __iter__(self) -> Iterator[str]:
        return iter(self._cfg)

    def __len__(self) -> int:
        return len(self._cfg)


class ParametersForTaskHydraService(ParametersForTaskService):
    _pipeline_config: PipelineConfigService

    def __init__(self, pipeline_config: PipelineConfigService) -> None:
        self._pipeline_config = pipeline_config

    def get_config(self, task: str, overrides: Sequence[str] = []) -> Mapping[str, Any] | None:
        task_cfg = self._pipeline_config(overrides=overrides).task_parameters.get(task)
        return (
            None
            if task_cfg is None or task_cfg.config is None
            else InstantiateConfMapping(DictConfig(task_cfg.config))
        )

    def get_service_ids(
        self, task: str, overrides: Sequence[str] = []
    ) -> Mapping[str, ServiceId[Any]] | None:
        task_cfg = self._pipeline_config(overrides=overrides).task_parameters.get(task)
        return (
            None
            if task_cfg is None or task_cfg.service_ids is None
            else InstantiateConfMapping(DictConfig(task_cfg.service_ids))
        )
