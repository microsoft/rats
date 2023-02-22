from functools import lru_cache

from oneml.processors import PipelineSessionProvider

from ._pipelines_container import OnemlHabitatsPipelinesDiContainer


class OnemlHabitatsProcessorsDiContainer:

    _pipelines_container: OnemlHabitatsPipelinesDiContainer

    def __init__(self, pipelines_container: OnemlHabitatsPipelinesDiContainer) -> None:
        self._pipelines_container = pipelines_container

    @lru_cache()
    def pipeline_session_provider(self) -> PipelineSessionProvider:
        return PipelineSessionProvider(
            builder_factory=self._pipelines_container.pipeline_builder_factory(),
            session_context=self._pipelines_container.pipeline_session_context(),
        )
