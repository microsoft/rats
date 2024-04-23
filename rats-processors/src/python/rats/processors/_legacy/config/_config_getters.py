from abc import abstractmethod
from collections.abc import Iterator, Mapping
from functools import cached_property
from pathlib import Path
from typing import Any, Protocol, cast

from hydra_zen import instantiate
from omegaconf import DictConfig, OmegaConf

from rats.services import ServiceId

from ._hydra_clients import PipelineConfigService

CONF_PATH = Path("src/resources/conf")


class IGetConfig(Protocol):
    @abstractmethod
    def get_config(self, name: str) -> Mapping[str, Any] | None: ...

    @abstractmethod
    def get_pipeline_config(self) -> dict[str, Any] | Any: ...


class IGetServiceId(Protocol):
    @abstractmethod
    def get_service_ids(self, name: str) -> Mapping[str, ServiceId[Any]] | None: ...


class IGetConfigAndServiceId(IGetConfig, IGetServiceId, Protocol):
    def get_config_and_service_ids(
        self, name: str
    ) -> tuple[Mapping[str, Any] | None, Mapping[str, ServiceId[Any]] | None]:
        return self.get_config(name), self.get_service_ids(name)


class InstantiateConfMapping(Mapping[str, Any]):
    _cfg: DictConfig

    def __init__(self, cfg: DictConfig) -> None:
        self._cfg = cfg

    # Note: Using a @cache or @lru_cache instead of @cached_property here causes infinite recursion
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


class HydraPipelineConfigService(IGetConfigAndServiceId):
    _pipeline_config_provider: PipelineConfigService

    def __init__(self, pipeline_config_provider: PipelineConfigService) -> None:
        self._pipeline_config_provider = pipeline_config_provider

    def get_config(self, name: str) -> Mapping[str, Any] | None:
        pipeline_config = self._pipeline_config_provider()
        cfg = pipeline_config.configs.get(name)
        return None if cfg is None else InstantiateConfMapping(DictConfig(cfg))

    def get_service_ids(self, name: str) -> Mapping[str, ServiceId[Any]] | None:
        pipeline_config = self._pipeline_config_provider()
        cfg = pipeline_config.service_ids.get(name)
        return None if cfg is None else InstantiateConfMapping(DictConfig(cfg))

    def get_pipeline_config(self) -> dict[str, Any] | Any:
        pipeline_config = self._pipeline_config_provider()
        return OmegaConf.to_container(pipeline_config.configs, resolve=True)
