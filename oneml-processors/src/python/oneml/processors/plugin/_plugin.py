from oneml.app import AppPlugin
from oneml.services import IManageServices

from ..config import OnemlProcessorsConfigPlugin
from ..dag import OnemlProcessorsDagPlugin
from ..io import OnemlProcessorsIoPlugin
from ..pipeline_operations import OnemlProcessorsPipelineOperationsPlugin
from ..training import OnemlProcessorsTrainingPlugin
from ..ux import OnemlProcessorsUxPlugin


class OnemlProcessorsPlugin(AppPlugin):
    def load_plugin(self, app: IManageServices) -> None:
        OnemlProcessorsIoPlugin().load_plugin(app)
        OnemlProcessorsDagPlugin().load_plugin(app)
        OnemlProcessorsUxPlugin().load_plugin(app)
        OnemlProcessorsPipelineOperationsPlugin().load_plugin(app)
        OnemlProcessorsTrainingPlugin().load_plugin(app)
        OnemlProcessorsConfigPlugin().load_plugin(app)
