import logging
from pathlib import Path

from rats.app import AppPlugin, RatsAppServices
from rats.processors._legacy_subpackages.registry import RatsProcessorsRegistryServices
from rats.services import (
    ContextId,
    IManageServices,
    IProvideServices,
    ServiceId,
    scoped_context_ids,
    scoped_service_ids,
    service_provider,
)

from ._config_getters import HydraPipelineConfigService, IGetConfigAndServiceId
from ._hydra_clients import HydraContext, HydraPipelineConfigServiceProvider, PipelineConfigService

logger = logging.getLogger(__name__)


@scoped_service_ids
class _PrivateServices:
    PIPELINE_CONFIG_SERVICE = ServiceId[PipelineConfigService]("pipeline-config-service")
    CONFIG_AND_SERVICEID_GETTER = ServiceId[IGetConfigAndServiceId]("config-and-service-id-getter")


class RatsProcessorsConfigDiContainer:
    _app: IProvideServices

    def __init__(self, app: IProvideServices) -> None:
        self._app = app

    def _parameters_config_dir(self) -> str:
        return str(Path("src/resources/params").absolute())

    @service_provider(_PrivateServices.PIPELINE_CONFIG_SERVICE)
    def pipeline_config_service(self) -> PipelineConfigService:
        context_client = self._app.get_service(RatsAppServices.APP_CONTEXT_CLIENT)
        hydra_pipeline_config_service_provider = HydraPipelineConfigServiceProvider(
            config_dir=self._parameters_config_dir(),
            context_provider=context_client.get_context_provider(
                RatsProcessorsConfigContexts.HYDRA
            ),
            pipeline_providers=self._app.get_service(
                RatsProcessorsRegistryServices.PIPELINE_PROVIDERS
            ),
        )
        return hydra_pipeline_config_service_provider()

    @service_provider(_PrivateServices.CONFIG_AND_SERVICEID_GETTER)
    def parameters_for_task_service(self) -> IGetConfigAndServiceId:
        pipeline_config_provider = self._app.get_service(
            RatsProcessorsConfigServices.PIPELINE_CONFIG_SERVICE
        )
        return HydraPipelineConfigService(pipeline_config_provider)


class RatsProcessorsConfigPlugin(AppPlugin):
    def load_plugin(self, app: IManageServices) -> None:
        logger.debug("initializing rats-processors-config plugin")
        app.parse_service_container(RatsProcessorsConfigDiContainer(app))


class RatsProcessorsConfigServices:
    PIPELINE_CONFIG_SERVICE = _PrivateServices.PIPELINE_CONFIG_SERVICE
    CONFIG_AND_SERVICEID_GETTER = _PrivateServices.CONFIG_AND_SERVICEID_GETTER


@scoped_context_ids
class RatsProcessorsConfigContexts:
    HYDRA = ContextId[HydraContext]("hydra")
