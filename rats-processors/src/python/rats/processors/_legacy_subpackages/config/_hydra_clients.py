from abc import abstractmethod
from functools import cache
from typing import Protocol

from hydra import compose, initialize_config_dir
from hydra.utils import instantiate
from hydra_zen import ZenStore
from typing_extensions import NamedTuple

from rats.processors._legacy_subpackages.registry import IProvidePipelineCollection
from rats.services import ContextProvider

from ..ux import register_resolvers
from ._schemas import GetPipelineFromProvider, PipelineConfig, register_configs


class HydraContext(NamedTuple):
    overrides: tuple[str, ...]


class PipelineConfigService(Protocol):
    @abstractmethod
    def __call__(self) -> PipelineConfig: ...


class HydraPipelineConfigService(PipelineConfigService):
    _config_dir: str
    _context_provider: ContextProvider[HydraContext]
    _pipeline_providers: IProvidePipelineCollection

    def __init__(
        self,
        config_dir: str,
        context_provider: ContextProvider[HydraContext],
        pipeline_providers: IProvidePipelineCollection,
    ) -> None:
        self._config_dir = config_dir
        self._context_provider = context_provider
        self._pipeline_providers = pipeline_providers

    @cache  # noqa: B019
    def _get_config_from_context(self, context: HydraContext) -> PipelineConfig:
        overrides = context.overrides
        with initialize_config_dir(config_dir=self._config_dir, version_base=None):
            cfg = compose(config_name="pipeline_config", overrides=list(overrides))
            icfg = instantiate(cfg, _recursive_=False, pipeline_providers=self._pipeline_providers)
            return icfg

    def __call__(self) -> PipelineConfig:
        context = self._context_provider()
        return self._get_config_from_context(context)


class HydraPipelineConfigServiceProvider:
    _config_dir: str
    _context_provider: ContextProvider[HydraContext]
    _pipeline_providers: IProvidePipelineCollection

    def __init__(
        self,
        config_dir: str,
        context_provider: ContextProvider[HydraContext],
        pipeline_providers: IProvidePipelineCollection,
    ) -> None:
        self._config_dir = config_dir
        self._context_provider = context_provider
        self._pipeline_providers = pipeline_providers

    def _register_configs(self) -> None:
        store = ZenStore(name="rats-processors-types")
        register_configs(store)
        store.add_to_hydra_store()

    def _register_pipeline_providers(self) -> None:
        store = ZenStore(name="pipeline-providers")
        for name in self._pipeline_providers:
            store(
                GetPipelineFromProvider(key=name),
                name=name,
                group="pipeline_ids",
            )
        store.add_to_hydra_store()

    @cache  # noqa: B019
    def __call__(self) -> HydraPipelineConfigService:
        register_resolvers()
        self._register_configs()
        self._register_pipeline_providers()
        return HydraPipelineConfigService(
            config_dir=self._config_dir,
            pipeline_providers=self._pipeline_providers,
            context_provider=self._context_provider,
        )
