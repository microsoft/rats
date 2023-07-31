import logging

from oneml.app import AppPlugin
from oneml.services import IManageServices

from ._di_container import OnemlProcessorsDiContainer

logger = logging.getLogger(__name__)


class OnemlProcessorsPlugin(AppPlugin):
    def load_plugin(self, app: IManageServices) -> None:
        app.parse_service_container(OnemlProcessorsDiContainer(app))
        # if isinstance(app, OnemlApp):
        #     logger.debug("initializing oneml-processors plugin")
        #     di_container = OnemlProcessorsDiContainer(app)
        #     app.parse_service_container(di_container)
        # else:
        #     logger.debug("skipping oneml-processors plugin b/c app is not an OnemlApp")
