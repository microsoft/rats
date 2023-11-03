from abc import abstractmethod
from functools import cache
from typing import NamedTuple, Protocol

from hydra import compose, initialize_config_dir
from hydra.utils import instantiate
from hydra_zen import ZenStore

from oneml.processors.pipeline_operations import OnemlProcessorsPipelineOperationsServices
from oneml.services import ContextProvider, IProvideServices

from ..ux import register_resolvers
from ._schemas import GetPipelineFromApp, PipelineConfig, ServiceIdConf, register_configs


class HydraContext(NamedTuple):
    overrides: tuple[str, ...]


class PipelineConfigService(Protocol):
    @abstractmethod
    def __call__(self) -> PipelineConfig:
        ...


class HydraPipelineConfigService(PipelineConfigService):
    _config_dir: str
    _app: IProvideServices
    _context_provider: ContextProvider[HydraContext]

    def __init__(
        self,
        config_dir: str,
        app: IProvideServices,
        context_provider: ContextProvider[HydraContext],
    ) -> None:
        self._config_dir = config_dir
        self._app = app
        self._context_provider = context_provider

    @cache
    def _get_config_from_context(self, context: HydraContext) -> PipelineConfig:
        overrides = context.overrides
        with initialize_config_dir(config_dir=self._config_dir, version_base=None):
            cfg = compose(config_name="pipeline_config", overrides=list(overrides))
            return instantiate(cfg, _recursive_=False, app=self._app)

    def __call__(self) -> PipelineConfig:
        context = self._context_provider()
        return self._get_config_from_context(context)


class RegisterPipelineProvidersToHydra:
    _app: IProvideServices
    _store: ZenStore

    def __init__(self, app: IProvideServices) -> None:
        self._app = app
        self._store = ZenStore(name="pipeline-providers")

    def __call__(self) -> None:
        pipeline_providers = self._app.get_service_group(
            OnemlProcessorsPipelineOperationsServices.PIPELINE_PROVIDER_IDS
        )
        for pipeline_provider_mapping in pipeline_providers:
            for name, pipeline_provider_id in pipeline_provider_mapping.items():
                self._store(
                    GetPipelineFromApp(service_id=ServiceIdConf(name=pipeline_provider_id.name)),
                    name=name,
                    group="pipeline_ids",
                )
        self._store.add_to_hydra_store()


class HydraPipelineConfigServiceProvider:
    _config_dir: str
    _app: IProvideServices
    _context_provider: ContextProvider[HydraContext]
    _pipeline_providers_registrar: RegisterPipelineProvidersToHydra

    def __init__(
        self,
        config_dir: str,
        app: IProvideServices,
        context_provider: ContextProvider[HydraContext],
        pipeline_providers_registrar: RegisterPipelineProvidersToHydra,
    ) -> None:
        self._config_dir = config_dir
        self._app = app
        self._context_provider = context_provider
        self._pipeline_providers_registrar = pipeline_providers_registrar

    def _register_configs(self) -> None:
        store = ZenStore(name="oneml-processors-types")
        register_configs(store)
        store.add_to_hydra_store()

    def _register_pipeline_providers(self) -> None:
        self._pipeline_providers_registrar()

    @cache
    def __call__(self) -> HydraPipelineConfigService:
        register_resolvers()
        self._register_configs()
        self._register_pipeline_providers()
        return HydraPipelineConfigService(
            config_dir=self._config_dir, app=self._app, context_provider=self._context_provider
        )
