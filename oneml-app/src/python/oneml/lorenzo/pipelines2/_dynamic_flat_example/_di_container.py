from functools import lru_cache

from oneml.lorenzo.pipelines import InMemoryStorage

from ._pipeline import MyPipelineOutput, MyPipelineProvider


class DynamicFlatExamplePipelineContainer:

    @lru_cache()
    def pipeline_provider(self) -> MyPipelineProvider:
        return MyPipelineProvider()

    @lru_cache()
    def _pipeline_output(self) -> MyPipelineOutput:
        return MyPipelineOutput(storage=self._storage())

    @lru_cache()
    def _storage(self) -> InMemoryStorage:
        return InMemoryStorage()
