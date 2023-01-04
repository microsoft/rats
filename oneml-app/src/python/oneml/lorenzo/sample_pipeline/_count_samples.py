import logging
from typing import Tuple

from oneml.lorenzo.sample_pipeline import Sample
from oneml.lorenzo.sample_pipeline._provider import SimpleProvider
from oneml.lorenzo.sample_pipeline._publisher import SimplePublisher
from oneml.pipelines.session import IExecutable

logger = logging.getLogger(__name__)


class CountSamples(IExecutable):
    _publisher: SimplePublisher[int]
    _input_provider: SimpleProvider[Tuple[Sample, ...]]

    def __init__(
        self,
        input_provider: SimpleProvider[Tuple[Sample, ...]],
        publisher: SimplePublisher[int],
    ) -> None:
        self._input_provider = input_provider
        self._publisher = publisher

    def execute(self) -> None:
        samples = self._input_provider.data()
        logger.info(f"found <{len(samples)}> samples in input data")
        self._publisher.publish(len(samples))
