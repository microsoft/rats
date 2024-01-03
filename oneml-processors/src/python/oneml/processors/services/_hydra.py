from abc import abstractmethod
from functools import cache
from typing import NamedTuple, Protocol

from hydra import compose, initialize_config_dir
from hydra.utils import instantiate
from hydra_zen import ZenStore

from oneml.services import ContextProvider

from .. import schemas, ux
from ..schemas import PipelineConfig


class HydraContext(NamedTuple):
    overrides: tuple[str, ...]


class PipelineConfigService(Protocol):
    @abstractmethod
    def __call__(self) -> PipelineConfig:
        ...


class HydraPipelineConfigService(PipelineConfigService):
    _config_dir: str
    _context_provider: ContextProvider[HydraContext]

    def __init__(self, config_dir: str, context_provider: ContextProvider[HydraContext]) -> None:
        self._config_dir = config_dir
        self._context_provider = context_provider

    @cache  # noqa: B019
    def _get_config_for_context(self, context: HydraContext) -> PipelineConfig:
        overrides = context.overrides
        with initialize_config_dir(config_dir=self._config_dir, version_base=None):
            cfg = compose(config_name="pipeline_config", overrides=list(overrides))
            return instantiate(cfg, _recursive_=False)

    def __call__(self) -> PipelineConfig:
        context = self._context_provider()
        return self._get_config_for_context(context)


class HydraPipelineConfigServiceProvider:
    _config_dir: str
    _context_provider: ContextProvider[HydraContext]
    _store: ZenStore

    def __init__(self, config_dir: str, context_provider: ContextProvider[HydraContext]) -> None:
        self._config_dir = config_dir
        self._context_provider = context_provider
        self._store = ZenStore(name="oneml-processors")

    def _register_resolvers_and_configs(self) -> None:
        ux.register_resolvers()
        schemas.register_configs(self._store)
        self._store.add_to_hydra_store()

    @cache  # noqa: B019
    def __call__(self) -> HydraPipelineConfigService:
        self._register_resolvers_and_configs()
        return HydraPipelineConfigService(
            config_dir=self._config_dir, context_provider=self._context_provider
        )
