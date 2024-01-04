import logging
from typing import cast

from oneml.app import AppPlugin
from oneml.processors.dag import OnemlProcessorsDagServices
from oneml.processors.registry import (
    IProvidePipeline,
    IProvidePipelineCollection,
    OnemlProcessorsRegistryServiceGroups,
    ServiceMapping,
)
from oneml.processors.ux import UPipeline
from oneml.services import (
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
            dag_submitter=self._app.get_service(OnemlProcessorsDagServices.DAG_SUBMITTER),
            diamond_provider=self._app.get_service(
                DiamondExampleServices.DIAMOND_PIPELINE_PROVIDER
            ),
        )

    @service_group(OnemlProcessorsRegistryServiceGroups.PIPELINE_PROVIDERS)
    def diamond_pipeline_providers_group(self) -> IProvidePipelineCollection:
        diamond = cast(
            ServiceId[IProvidePipeline[UPipeline]],
            _PrivateServices.DIAMOND_PIPELINE_PROVIDER,
        )
        return ServiceMapping(services_provider=self._app, service_ids_map={"diamond": diamond})


class OnemlProcessorsExamplePlugin(AppPlugin):
    def load_plugin(self, app: IManageServices) -> None:
        logger.debug("initializing oneml-processors-io plugin")
        app.parse_service_container(DiamondExampleDiContainer(app))


class DiamondExampleServices:
    DIAMOND_EXECUTABLE = _PrivateServices.DIAMOND_EXECUTABLE
    DIAMOND_PIPELINE_PROVIDER = _PrivateServices.DIAMOND_PIPELINE_PROVIDER
