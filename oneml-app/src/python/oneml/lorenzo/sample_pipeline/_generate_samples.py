import hashlib
import logging
import os
from typing import Dict, Tuple

from oneml.pipelines.dag import PipelinePort
from oneml.pipelines.session import IExecutable

from ._publisher import SimplePublisher

logger = logging.getLogger(__name__)

ExampleSamplesPort = PipelinePort[Tuple[Dict[str, str], ...]]("__main__")


class GenerateSamples(IExecutable):
    _publisher: SimplePublisher[Tuple[Dict[str, str], ...]]

    def __init__(self, presenter: SimplePublisher[Tuple[Dict[str, str], ...]]) -> None:
        self._publisher = presenter

    def execute(self) -> None:
        logger.info(f"Executing! {self}")
        samples = []
        for x in range(100):
            sample = dict(
                name=f"sample-{x}",
                value=hashlib.md5(str(x).encode()).hexdigest(),
            )
            samples.append(sample)

        logger.info(f"pod name: {os.environ.get('POD_NAME', 'N/A')}")

        self._publisher.publish(tuple(samples))
