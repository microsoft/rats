import logging

from rats.pipelines.dag import PipelineDagClient
from rats.pipelines.session import RatsSessionContexts
from rats.services import IManageServices, service_provider

from ._rats_app_services import RatsAppServices

logger = logging.getLogger(__name__)


class RatsDagDiContainer:
    _app: IManageServices

    def __init__(self, app: IManageServices) -> None:
        self._app = app

    @service_provider(RatsAppServices.PIPELINE_DAG_CLIENT)
    def pipeline_dag_client(self) -> PipelineDagClient:
        client = self._app.get_service(RatsAppServices.APP_CONTEXT_CLIENT)
        return PipelineDagClient(
            context=client.get_context_provider(RatsSessionContexts.PIPELINE),
        )
