import logging
import time

from oneml.lorenzo.pipelines3 import IExecutable

logger = logging.getLogger(__name__)


class PauseStep(IExecutable):
    _seconds: int

    def __init__(self, seconds: int):
        self._seconds = seconds

    def execute(self) -> None:
        logger.debug(f"Running PauseStep(seconds={self._seconds})")
        for x in range(self._seconds):
            logger.debug(f"Sleeping: {x}")
            time.sleep(1)
