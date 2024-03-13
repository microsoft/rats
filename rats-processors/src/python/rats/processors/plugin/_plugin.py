from rats.app import AppPlugin
from rats.services import IManageServices

from ..config import RatsProcessorsConfigPlugin
from ..dag import RatsProcessorsDagPlugin
from ..io import RatsProcessorsIoPlugin
from ..pipeline_operations import RatsProcessorsPipelineOperationsPlugin
from ..registry import RatsProcessorsRegistryPlugin
from ..training import RatsProcessorsTrainingPlugin
from ..ux import RatsProcessorsUxPlugin


class RatsProcessorsPlugin(AppPlugin):
    def load_plugin(self, app: IManageServices) -> None:
        RatsProcessorsIoPlugin().load_plugin(app)
        RatsProcessorsDagPlugin().load_plugin(app)
        RatsProcessorsUxPlugin().load_plugin(app)
        RatsProcessorsPipelineOperationsPlugin().load_plugin(app)
        RatsProcessorsTrainingPlugin().load_plugin(app)
        RatsProcessorsConfigPlugin().load_plugin(app)
        RatsProcessorsRegistryPlugin().load_plugin(app)
