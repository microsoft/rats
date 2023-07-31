import logging

from oneml.app import AppPlugin
from oneml.services import IManageServices

from ._di_container import OnemlHabitatsDiContainer

logger = logging.getLogger(__name__)


class OnemlHabitatsPlugin(AppPlugin):
    def load_plugin(self, app: IManageServices) -> None:
        logger.debug("initializing oneml-habitats plugin")
        di_container = OnemlHabitatsDiContainer(app)
        app.parse_service_container(di_container)
