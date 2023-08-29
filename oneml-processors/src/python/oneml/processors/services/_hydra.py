from abc import abstractmethod
from functools import cache
from typing import Protocol, Sequence

from hydra import compose, initialize_config_dir
from hydra.utils import instantiate
from hydra_zen import ZenStore

from .. import schemas, ux
from ..schemas import PipelineConfig


class PipelineConfigService(Protocol):
    @abstractmethod
    def __call__(self, overrides: Sequence[str] = ()) -> PipelineConfig:
        ...


class HydraPipelineConfigService(PipelineConfigService):
    _config_dir: str

    def __init__(self, config_dir: str) -> None:
        self._config_dir = config_dir

    @cache
    def __call__(self, overrides: Sequence[str] = []) -> PipelineConfig:
        with initialize_config_dir(config_dir=self._config_dir, version_base=None):
            cfg = compose(config_name="pipeline_config", overrides=list(overrides))
            return instantiate(cfg, _recursive_=False)


class HydraPipelineConfigServiceProvider:
    _config_dir: str
    _store: ZenStore

    def __init__(self, config_dir: str) -> None:
        self._config_dir = config_dir
        self._store = ZenStore(name="oneml-processors")

    def _register_resolvers_and_configs(self) -> None:
        ux.register_resolvers()
        schemas.register_configs(self._store)
        self._store.add_to_hydra_store()

    @cache
    def __call__(self) -> HydraPipelineConfigService:
        self._register_resolvers_and_configs()
        return HydraPipelineConfigService(self._config_dir)
