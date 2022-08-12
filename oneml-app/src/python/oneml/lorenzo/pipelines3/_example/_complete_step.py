import logging

from oneml.pipelines import IExecutable, IStopPipelines

logger = logging.getLogger(__name__)


class CompleteStep(IExecutable):
    _target: IStopPipelines

    def __init__(self, target: IStopPipelines):
        self._target = target

    def execute(self) -> None:
        logger.debug(f"Running CompleteStep(target={self._target})")
        self._target.stop_pipeline()
