import logging

from oneml.app import AppPlugin
from oneml.habitats.io import OnemlHabitatsIoPlugin
from oneml.habitats.pipeline_operations import OnemlHabitatsPipelineOperationsPlugin
from oneml.services import IManageServices

logger = logging.getLogger(__name__)


class OnemlHabitatsPlugin(AppPlugin):
    def load_plugin(self, app: IManageServices) -> None:
        logger.debug("initializing oneml-habitats plugin")

        OnemlHabitatsIoPlugin().load_plugin(app)
        OnemlHabitatsPipelineOperationsPlugin().load_plugin(app)
