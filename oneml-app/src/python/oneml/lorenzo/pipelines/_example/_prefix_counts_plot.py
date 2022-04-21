from matplotlib import pyplot

from oneml.lorenzo.pipelines import PipelineStep, PipelineDataWriter
from ._prefix_counts import SamplePrefixCounts


class SamplePrefixCountPlotStep(PipelineStep):

    _storage: PipelineDataWriter
    _sample_prefix_counts: SamplePrefixCounts

    def __init__(self, storage: PipelineDataWriter, sample_prefix_counts: SamplePrefixCounts):
        self._storage = storage
        self._sample_prefix_counts = sample_prefix_counts

    def execute(self) -> None:
        labels = []
        values = []
        for label, value in self._sample_prefix_counts.top(10):
            labels.append(label)
            values.append(value)

        fig, ax = pyplot.subplots()
        ax.pie(values, labels=labels, shadow=True, autopct="%1.1f%%")
        ax.axis("equal")
