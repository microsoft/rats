from oneml.app import AppPlugin
from oneml.services import IManageServices

from ..pipeline_operations import OnemlProcessorsPipelineOperationsPlugin
from ._di_container import OnemlProcessorsDiContainer


class OnemlProcessorsPlugin(AppPlugin):
    def load_plugin(self, app: IManageServices) -> None:
        app.parse_service_container(OnemlProcessorsDiContainer(app))

        OnemlProcessorsPipelineOperationsPlugin().load_plugin(app)
