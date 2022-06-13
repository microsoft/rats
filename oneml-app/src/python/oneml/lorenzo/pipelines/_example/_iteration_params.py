from dataclasses import dataclass
from typing import Tuple

from oneml.lorenzo.pipelines import PipelineDataWriter, PipelineStep

from ._fake_samples import FakeSamplesStepConfig


@dataclass(frozen=True)
class IterationParameters:
    num_samples: int
    prefix_length: int
    letters_to_count: Tuple[str, ...]


class IterationParametersStep(PipelineStep):
    _output_storage: PipelineDataWriter
    _iteration_number: int

    def __init__(self, output_storage: PipelineDataWriter, iteration_number: int):
        self._output_storage = output_storage
        self._iteration_number = iteration_number

    def execute(self) -> None:
        params = IterationParameters(
            num_samples=100,
            prefix_length=self._iteration_number + 1,
            letters_to_count=tuple(["a", "e", "i", "o", "u"]),
        )
        fake_samples_config = FakeSamplesStepConfig(num_samples=100)

        self._output_storage.save(IterationParameters, params)
