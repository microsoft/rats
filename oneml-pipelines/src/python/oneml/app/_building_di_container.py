from oneml.pipelines.building import PipelineBuilderClient
from oneml.services import IProvideServices, service_provider

from ._building_services import OnemlBuildingServices
from ._oneml_app_services import OnemlAppServices
from ._session_services import OnemlSessionServices


class OnemlBuildingDiContainer:
    _app: IProvideServices

    def __init__(self, app: IProvideServices) -> None:
        self._app = app

    @service_provider(OnemlBuildingServices.PIPELINE_BUILDER_CLIENT)
    @service_provider(OnemlAppServices.PIPELINE_BUILDER)
    def session_pipeline_builder(self) -> PipelineBuilderClient:
        return PipelineBuilderClient(
            dag_client=self._app.get_service(OnemlAppServices.PIPELINE_DAG_CLIENT),
            executables_client=self._app.get_service(OnemlSessionServices.NODE_EXECUTABLES_CLIENT),
        )
