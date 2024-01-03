from abc import abstractmethod
from collections.abc import Iterator, Mapping
from functools import cached_property
from pathlib import Path
from typing import Any, Protocol, cast

from hydra_zen import instantiate
from omegaconf import DictConfig

from oneml.processors.schemas.configs import TaskParametersConf
from oneml.services import ServiceId

from ._hydra import PipelineConfigService

CONF_PATH = Path("src/resources/conf")


class ConfigsForTaskService(Protocol):
    @abstractmethod
    def get_config(self, task: str) -> Mapping[str, Any] | None:
        ...


class ServiceIdsForTaskService(Protocol):
    @abstractmethod
    def get_service_ids(self, task: str) -> Mapping[str, ServiceId[Any]] | None:
        ...


class ParametersForTaskService(ConfigsForTaskService, ServiceIdsForTaskService):
    def get_config_and_service_ids(
        self, task: str
    ) -> tuple[Mapping[str, Any] | None, Mapping[str, ServiceId[Any]] | None]:
        return self.get_config(task), self.get_service_ids(task)


class InstantiateConfMapping(Mapping[str, Any]):
    _cfg: DictConfig

    def __init__(self, cfg: DictConfig) -> None:
        self._cfg = cfg

    # Note: Using a @cache or @lru_cache instead of @cached_property here causes inifinte recursion
    # when the second object of the class is used.  This is probably b/c the cache is created at
    # the class level, and self is a key in the cache, and so calling __getitem__ requires
    # comparing self to the cache key which requires calling __getitem__ recursively.
    @cached_property
    def _instantiated(self) -> Mapping[str, Any]:
        return instantiate(self._cfg)

    def __getitem__(self, key: str) -> Any:
        return self._instantiated[key]

    def __contains__(self, key: object) -> bool:
        return key in self._cfg

    def __hash__(self) -> int:
        return hash(self._cfg)

    def __iter__(self) -> Iterator[str]:
        return iter(self._cfg)

    def __len__(self) -> int:
        return len(self._cfg)

    def __getstate__(self) -> Any:
        # @cached_property creates a field on the object, and we don't want to serialize that.
        return self._cfg

    def __setstate__(self, state: Any) -> None:
        self._cfg = cast(DictConfig, state)


class ParametersForTaskHydraService(ParametersForTaskService):
    _pipeline_config_provider: PipelineConfigService

    def __init__(self, pipeline_config_provider: PipelineConfigService) -> None:
        self._pipeline_config_provider = pipeline_config_provider

    def _get_task_cfg(self, task: str) -> TaskParametersConf | None:
        pipeline_config = self._pipeline_config_provider()
        return pipeline_config.task_parameters.get(task)

    def get_config(self, task: str) -> Mapping[str, Any] | None:
        task_cfg = self._get_task_cfg(task)
        return (
            None
            if task_cfg is None or task_cfg.config is None
            else InstantiateConfMapping(DictConfig(task_cfg.config))
        )

    def get_service_ids(self, task: str) -> Mapping[str, ServiceId[Any]] | None:
        task_cfg = self._get_task_cfg(task)
        return (
            None
            if task_cfg is None or task_cfg.service_ids is None
            else InstantiateConfMapping(DictConfig(task_cfg.service_ids))
        )
