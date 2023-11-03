import logging
from typing import Mapping

from oneml.processors.dag import OnemlProcessorsDagServices
from oneml.processors.pipeline_operations import (
    ExecutablePipeline,
    IProvidePipeline,
    OnemlProcessorsPipelineOperationsServices,
)
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

    @service_group(OnemlProcessorsPipelineOperationsServices.PIPELINE_PROVIDER_IDS)  # type: ignore[arg-type]
    @service_group(OnemlProcessorsPipelineOperationsServices.EXECUTABLE_PIPELINE_PROVIDER_IDS)
    def diamond_pipeline_providers_group(
        self,
    ) -> Mapping[str, ServiceId[IProvidePipeline[ExecutablePipeline]]]:
        return {"diamond": DiamondExampleServices.DIAMOND_PIPELINE_PROVIDER}  # type: ignore[dict-item]
