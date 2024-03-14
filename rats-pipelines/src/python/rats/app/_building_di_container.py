from rats.pipelines.building import PipelineBuilderClient
from rats.services import IProvideServices, service_provider

from ._building_services import RatsBuildingServices
from ._rats_app_services import RatsAppServices
from ._session_services import RatsSessionServices


class RatsBuildingDiContainer:
    _app: IProvideServices

    def __init__(self, app: IProvideServices) -> None:
        self._app = app

    @service_provider(RatsBuildingServices.PIPELINE_BUILDER_CLIENT)
    @service_provider(RatsAppServices.PIPELINE_BUILDER)
    def session_pipeline_builder(self) -> PipelineBuilderClient:
        return PipelineBuilderClient(
            dag_client=self._app.get_service(RatsAppServices.PIPELINE_DAG_CLIENT),
            executables_client=self._app.get_service(RatsSessionServices.NODE_EXECUTABLES_CLIENT),
        )
