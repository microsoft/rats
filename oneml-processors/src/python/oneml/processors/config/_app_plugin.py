import logging
from pathlib import Path

from oneml.app import AppPlugin, OnemlAppServices
from oneml.processors.registry import OnemlProcessorsRegistryServices
from oneml.services import (
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


class OnemlProcessorsConfigDiContainer:
    _app: IProvideServices

    def __init__(self, app: IProvideServices) -> None:
        self._app = app

    def _parameters_config_dir(self) -> str:
        return str(Path("src/resources/params").absolute())

    @service_provider(_PrivateServices.PIPELINE_CONFIG_SERVICE)
    def pipeline_config_service(self) -> PipelineConfigService:
        context_client = self._app.get_service(OnemlAppServices.APP_CONTEXT_CLIENT)
        hydra_pipeline_config_service_provider = HydraPipelineConfigServiceProvider(
            config_dir=self._parameters_config_dir(),
            context_provider=context_client.get_context_provider(
                OnemlProcessorsConfigContexts.HYDRA
            ),
            pipeline_providers=self._app.get_service(
                OnemlProcessorsRegistryServices.PIPELINE_PROVIDERS
            ),
        )
        return hydra_pipeline_config_service_provider()

    @service_provider(_PrivateServices.CONFIG_AND_SERVICEID_GETTER)
    def parameters_for_task_service(self) -> IGetConfigAndServiceId:
        pipeline_config_provider = self._app.get_service(
            OnemlProcessorsConfigServices.PIPELINE_CONFIG_SERVICE
        )
        return HydraPipelineConfigService(pipeline_config_provider)


class OnemlProcessorsConfigPlugin(AppPlugin):
    def load_plugin(self, app: IManageServices) -> None:
        logger.debug("initializing oneml-processors-config plugin")
        app.parse_service_container(OnemlProcessorsConfigDiContainer(app))


class OnemlProcessorsConfigServices:
    PIPELINE_CONFIG_SERVICE = _PrivateServices.PIPELINE_CONFIG_SERVICE
    CONFIG_AND_SERVICEID_GETTER = _PrivateServices.CONFIG_AND_SERVICEID_GETTER


@scoped_context_ids
class OnemlProcessorsConfigContexts:
    HYDRA = ContextId[HydraContext]("hydra")
