import logging

from rats.app_api import AppPlugin
from rats.services import IManageServices

logger = logging.getLogger(__name__)


class RatsAppNoopPlugin(AppPlugin):
    def load_plugin(self, app: IManageServices) -> None:
        logger.debug(f"no-op plugin activating for app: {app}")
