import logging
from typing import cast

from rats.app import AppPlugin
from rats.processors._legacy_subpackages.dag import RatsProcessorsDagServices
from rats.processors._legacy_subpackages.registry import (
    IProvidePipeline,
    IProvidePipelineCollection,
    RatsProcessorsRegistryServiceGroups,
    ServiceMapping,
)
from rats.processors._legacy_subpackages.ux import UPipeline
from rats.services import (
    IExecutable,
    IManageServices,
    IProvideServices,
    ServiceId,
    scoped_service_ids,
    service_group,
    service_provider,
)

from ._pipeline import DiamondExecutable, DiamondPipeline, DiamondPipelineProvider

logger = logging.getLogger(__name__)


@scoped_service_ids
class _PrivateServices:
    DIAMOND_EXECUTABLE = ServiceId[IExecutable]("diamond-executable")
    DIAMOND_PIPELINE_PROVIDER = ServiceId[IProvidePipeline[DiamondPipeline]]("diamond-provider")


class DiamondExampleDiContainer:
    _app: IProvideServices

    def __init__(self, app: IProvideServices) -> None:
        self._app = app

    @service_provider(_PrivateServices.DIAMOND_PIPELINE_PROVIDER)
    def diamond_pipeline_provider(self) -> DiamondPipelineProvider:
        return DiamondPipelineProvider()

    @service_provider(_PrivateServices.DIAMOND_EXECUTABLE)
    def diamond_executable_pipeline(self) -> DiamondExecutable:
        return DiamondExecutable(
            dag_submitter=self._app.get_service(RatsProcessorsDagServices.DAG_SUBMITTER),
            diamond_provider=self._app.get_service(
                DiamondExampleServices.DIAMOND_PIPELINE_PROVIDER
            ),
        )

    @service_group(RatsProcessorsRegistryServiceGroups.PIPELINE_PROVIDERS)
    def diamond_pipeline_providers_group(self) -> IProvidePipelineCollection:
        diamond = cast(
            ServiceId[IProvidePipeline[UPipeline]],
            _PrivateServices.DIAMOND_PIPELINE_PROVIDER,
        )
        return ServiceMapping(services_provider=self._app, service_ids_map={"diamond": diamond})


class RatsProcessorsExamplePlugin(AppPlugin):
    def load_plugin(self, app: IManageServices) -> None:
        logger.debug("initializing rats-processors-io plugin")
        app.parse_service_container(DiamondExampleDiContainer(app))


class DiamondExampleServices:
    DIAMOND_EXECUTABLE = _PrivateServices.DIAMOND_EXECUTABLE
    DIAMOND_PIPELINE_PROVIDER = _PrivateServices.DIAMOND_PIPELINE_PROVIDER
