from functools import lru_cache

from immunodata.cli import ILocateDiContainers

from oneml.processors import PersistFittedEvalPipeline, PipelineSessionProvider
from oneml.processors.services import GetActiveNodeKey
from oneml.processors.ux._session import PipelineRunnerFactory

from ._pipelines_container import OnemlHabitatsPipelinesDiContainer


class OnemlHabitatsProcessorsDiContainer:
    _app: ILocateDiContainers

    def __init__(self, app: ILocateDiContainers):
        self._app = app

    @lru_cache()
    def pipeline_session_provider(self) -> PipelineSessionProvider:
        return PipelineSessionProvider(
            builder_factory=self._pipelines_container().pipeline_builder_factory(),
            session_context=self._pipelines_container().pipeline_session_context(),
        )

    @lru_cache()
    def pipeline_runner_factory(self) -> PipelineRunnerFactory:
        return PipelineRunnerFactory(pipeline_session_provider=self.pipeline_session_provider())

    def get_active_node_key_service(self) -> GetActiveNodeKey:
        return GetActiveNodeKey(self._pipelines_container().pipeline_session_context())

    def persist_fitted_eval_pipeline(self) -> PersistFittedEvalPipeline:
        return PersistFittedEvalPipeline(
            type_to_io_manager_mapping=self._pipelines_container()._default_datatype_iomanager_mapper()
        )

    def _pipelines_container(self) -> OnemlHabitatsPipelinesDiContainer:
        return self._app.find_container(OnemlHabitatsPipelinesDiContainer)
