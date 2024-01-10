import logging

from oneml.app import AppPlugin
from oneml.processors.utils import ImmutableNoOverlapChainMap
from oneml.services import (
    IManageServices,
    IProvideServices,
    ServiceId,
    scoped_service_ids,
    service_provider,
)

from ._pipeline_provider import IProvidePipelineCollection

logger = logging.getLogger(__name__)


@scoped_service_ids
class _PrivateServices:
    PIPELINE_PROVIDERS = ServiceId[IProvidePipelineCollection]("pipeline-providers")


@scoped_service_ids
class _PrivateServiceGroups:
    PIPELINE_PROVIDERS = ServiceId[IProvidePipelineCollection]("pipeline-providers")


class OnemlProcessorsRegistryDiContainer:
    _app: IProvideServices

    def __init__(self, app: IProvideServices) -> None:
        self._app = app

    @service_provider(_PrivateServices.PIPELINE_PROVIDERS)
    def pipeline_providers(self) -> IProvidePipelineCollection:
        maps = self._app.get_service_group(_PrivateServiceGroups.PIPELINE_PROVIDERS)
        return ImmutableNoOverlapChainMap(*maps)


class OnemlProcessorsRegistryPlugin(AppPlugin):
    def load_plugin(self, app: IManageServices) -> None:
        logger.debug("initializing oneml-processors-registry plugin")
        app.parse_service_container(OnemlProcessorsRegistryDiContainer(app))


class OnemlProcessorsRegistryServiceGroups:
    PIPELINE_PROVIDERS = _PrivateServiceGroups.PIPELINE_PROVIDERS


class OnemlProcessorsRegistryServices:
    PIPELINE_PROVIDERS = _PrivateServices.PIPELINE_PROVIDERS
