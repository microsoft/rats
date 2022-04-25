from oneml.lorenzo.pipelines import PipelineStep, PipelineStorage, TypeNamespaceClient, DeferredChainBuilder
from ._fake_samples import FakeSamplesStep
from ._sample import ExampleSamplesCollection
from ._prefix_counts import SamplePrefixCounts, SampleLetterCountStep
from ._prefix_counts_plot import SamplePrefixCountPlotStep
from ._iteration_params import IterationParameters


class ExamplePipelineIteration(PipelineStep):
    _storage: PipelineStorage
    _namespace_client: TypeNamespaceClient
    _parameters: IterationParameters

    def __init__(
            self,
            storage: PipelineStorage,
            namespace_client: TypeNamespaceClient,
            parameters: IterationParameters):
        self._storage = storage
        self._namespace_client = namespace_client
        self._parameters = parameters

    def execute(self) -> None:
        builder = DeferredChainBuilder()

        builder.add(lambda: FakeSamplesStep(
            # TODO: how do we decouple from storage output?
            storage=self._storage,
            num_samples=self._parameters.num_samples))

        # What if we want to run SampleSuffixCountStep instead of this step?
        # builder.add(lambda: SamplePrefixCountStep(
        #     storage=self._storage,
        #     prefix_length=self._parameters.prefix_length,
        #     samples=self._storage.load(ExampleSamplesCollection)))
        builder.add(lambda: SampleLetterCountStep(
            # This requires us to know that the input data to this task is the output of the
            # previous task
            storage=self._storage,
            prefix_length=self._parameters.prefix_length,
            letters_to_count=self._parameters.letters_to_count,
            samples=self._storage.load(ExampleSamplesCollection)))

        # Same input here regardless of the middle step (middle steps always produce same data class)
        builder.add(lambda: SamplePrefixCountPlotStep(
            storage=self._storage,
            sample_prefix_counts=self._storage.load(SamplePrefixCounts)))

        builder.build().execute()


"""

"""
