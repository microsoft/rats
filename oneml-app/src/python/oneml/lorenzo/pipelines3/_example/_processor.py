import logging
from typing import Dict

logger = logging.getLogger(__name__)


class SomeProcessor:
    def process(self, some_data: Dict[str, str]) -> None:
        # do the logic and return result. We do not know about folds here, just data
        logger.info(some_data)
