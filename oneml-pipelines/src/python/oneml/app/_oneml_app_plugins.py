import logging

from oneml.app_api import AppPlugin
from oneml.services import IManageServices

logger = logging.getLogger(__name__)


class OnemlAppNoopPlugin(AppPlugin):
    def load_plugin(self, app: IManageServices) -> None:
        logger.debug(f"no-op plugin activating for app: {app}")
