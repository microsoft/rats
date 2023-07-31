import logging

from oneml.pipelines.dag import PipelineDagClient
from oneml.pipelines.session import OnemlSessionContexts
from oneml.services import IManageServices, service_provider

from ._oneml_app_services import OnemlAppServices

logger = logging.getLogger(__name__)


class OnemlDagDiContainer:
    _app: IManageServices

    def __init__(self, app: IManageServices) -> None:
        self._app = app

    @service_provider(OnemlAppServices.PIPELINE_DAG_CLIENT)
    def pipeline_dag_client(self) -> PipelineDagClient:
        client = self._app.get_service(OnemlAppServices.APP_CONTEXT_CLIENT)
        return PipelineDagClient(
            context=client.get_context_provider(OnemlSessionContexts.PIPELINE),
        )
