import logging

from oneml.processors.services import OnemlProcessorsServices
from oneml.services import IProvideServices, service_provider

from ._pipeline import DiamondExampleServices, DiamondPipeline

logger = logging.getLogger(__name__)


class DiamondExampleDiContainer:
    _app: IProvideServices

    def __init__(self, app: IProvideServices) -> None:
        self._app = app

    @service_provider(DiamondExampleServices.DIAMOND)
    def pipeline(self) -> DiamondPipeline:
        return DiamondPipeline(
            dag_submitter=self._app.get_service(OnemlProcessorsServices.DAG_SUBMITTER),
        )
