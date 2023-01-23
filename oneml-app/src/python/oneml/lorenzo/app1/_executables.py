from typing import Any

from oneml.lorenzo.sample_pipeline import GenerateSamples
from oneml.lorenzo.sample_pipeline._count_samples import CountSamples
from oneml.lorenzo.sample_pipeline._provider import SimpleProvider
from oneml.lorenzo.sample_pipeline._publisher import SimplePublisher


class App1PipelineExecutables:

    _input_provider: SimpleProvider[Any]
    _output_presenter: SimplePublisher[Any]

    def __init__(
        self,
        input_provider: SimpleProvider[Any],
        output_presenter: SimplePublisher[Any],
    ) -> None:
        self._input_provider = input_provider
        self._output_presenter = output_presenter

    def generate_samples(self) -> GenerateSamples:
        return GenerateSamples(self._output_presenter)

    def count_samples(self) -> CountSamples:
        return CountSamples(self._input_provider, self._output_presenter)
