import logging
from typing import Mapping, cast

from oneml.processors.dag import OnemlProcessorsDagServices
from oneml.processors.registry import (
    IProvidePipeline,
    IProvidePipelineCollection,
    OnemlProcessorsRegistryServiceGroups,
    ServiceMapping,
)
from oneml.processors.ux import UPipeline
from oneml.services import IProvideServices, ServiceId, service_group, service_provider

from ._pipeline import DiamondExampleServices, DiamondExecutable, DiamondPipelineProvider

logger = logging.getLogger(__name__)


class DiamondExampleDiContainer:
    _app: IProvideServices

    def __init__(self, app: IProvideServices) -> None:
        self._app = app

    @service_provider(DiamondExampleServices.DIAMOND_PIPELINE_PROVIDER)
    def diamond_pipeline_provider(self) -> DiamondPipelineProvider:
        return DiamondPipelineProvider()

    @service_provider(DiamondExampleServices.DIAMOND_EXECUTABLE)
    def diamond_executable_pipeline(self) -> DiamondExecutable:
        return DiamondExecutable(
            dag_submitter=self._app.get_service(OnemlProcessorsDagServices.DAG_SUBMITTER),
            diamond_provider=self._app.get_service(
                DiamondExampleServices.DIAMOND_PIPELINE_PROVIDER
            ),
        )

    @service_group(OnemlProcessorsRegistryServiceGroups.PIPELINE_PROVIDERS)
    def diamond_pipeline_providers_group(
        self,
    ) -> IProvidePipelineCollection:
        diamond = cast(
            ServiceId[IProvidePipeline[UPipeline]],
            DiamondExampleServices.DIAMOND_PIPELINE_PROVIDER,
        )
        return ServiceMapping(
            services_provider=self._app,
            service_ids_map=dict(
                diamond=diamond,
            ),
        )
