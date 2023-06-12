import logging

from oneml.app import OnemlApp, OnemlAppPlugin
from oneml.services import IManageServices

from ._di_container import OnemlProcessorsDiContainer

logger = logging.getLogger(__name__)


class OnemlProcessorsPlugin(OnemlAppPlugin):
    def load_plugin(self, app: IManageServices) -> None:
        if isinstance(app, OnemlApp):
            logger.debug("initializing oneml-processors plugin")
            di_container = OnemlProcessorsDiContainer(app)
            app.parse_service_container(di_container)
        else:
            logger.debug("skipping oneml-processors plugin b/c app is not an OnemlApp")
