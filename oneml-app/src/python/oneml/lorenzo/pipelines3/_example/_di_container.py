from functools import lru_cache
from typing import Callable, Dict, Tuple

from oneml.lorenzo.logging import LoggingClient
from oneml.lorenzo.pipelines3 import (
    IExecutable,
    MlPipelineConfig,
    MlPipelineProvider,
    NullPipeline,
    PipelineNode,
    PipelineSession,
    StorageClient,
)

from ._application import Pipeline3ExampleApplication
from ._data_step import DataConsumerStep, DataProducerStep
from ._pause_step import PauseStep


class Pipeline3DiContainer:

    _args: Tuple[str, ...]

    def __init__(self, args: Tuple[str, ...]):
        self._args = args

    @lru_cache()
    def application(self) -> IExecutable:
        return Pipeline3ExampleApplication(
            logging_client=self._logging_client(),
            args=self._args,
            pipeline_session=self._pipeline_session(),
            pipeline_provider=self._example_pipeline_provider(),
        )

    @lru_cache()
    def _logging_client(self) -> LoggingClient:
        return LoggingClient()

    @lru_cache()
    def _example_pipeline_provider(self) -> MlPipelineProvider:
        return MlPipelineProvider(
            pipeline_config=MlPipelineConfig(
                executables_provider=self._example_pipeline_nodes,
                dependencies_provider=self._example_pipeline_dependencies,
                session_provider=self._pipeline_session,
            ),
        )

    @lru_cache()
    def _example_pipeline_nodes(self) -> Dict[PipelineNode, Callable[[], IExecutable]]:
        return {
            PipelineNode("pause-1"): lambda: PauseStep(1),
            PipelineNode("pause-3"): lambda: PauseStep(3),
            PipelineNode("data-1"): lambda: DataProducerStep(self._pipeline_storage()),
            PipelineNode("data-2"): lambda: DataConsumerStep(self._pipeline_storage()),
        }

    @lru_cache()
    def _example_pipeline_dependencies(self) -> Dict[PipelineNode, Tuple[PipelineNode, ...]]:
        return {
            PipelineNode("pause-1"): tuple([PipelineNode("pause-3")])
        }

    @lru_cache()
    def _pipeline_storage(self) -> StorageClient:
        return StorageClient()

    @lru_cache()
    def _pipeline_session(self) -> PipelineSession:
        return PipelineSession(pipeline=NullPipeline())
