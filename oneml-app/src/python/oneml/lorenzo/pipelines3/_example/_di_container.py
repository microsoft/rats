# type: ignore
# flake8: noqa
from functools import lru_cache
from typing import Callable, Dict, Tuple

from oneml.lorenzo.logging import LoggingClient
from oneml.pipelines import IExecutable, PipelineNode, PipelineNodeClient, PipelineNodeStateClient

from ._application import Pipeline3ExampleApplication
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
        )

    @lru_cache()
    def _logging_client(self) -> LoggingClient:
        return LoggingClient()

    @lru_cache()
    def _example_node_client(self) -> PipelineNodeClient:
        return PipelineNodeClient()

    @lru_cache()
    def _example_state_client(self) -> PipelineNodeStateClient:
        return PipelineNodeStateClient()

    @lru_cache()
    def _example_pipeline_nodes(self) -> Dict[PipelineNode, Callable[[], IExecutable]]:
        return {
            PipelineNode("data-prep.1"): lambda: PauseStep(1),
            PipelineNode("data-prep.2"): lambda: PauseStep(3),
            PipelineNode("data-prep.3"): lambda: PauseStep(2),
            PipelineNode("thing-doer.1"): lambda: PauseStep(4),
            PipelineNode("thing-doer.2"): lambda: PauseStep(2),
            PipelineNode("thing-doer.3"): lambda: PauseStep(3),
            PipelineNode("thing-doer.4"): lambda: PauseStep(3),
            PipelineNode("result-eval.1"): lambda: PauseStep(2),
        }

    @lru_cache()
    def _example_pipeline_dependencies(self) -> Dict[PipelineNode, Tuple[PipelineNode, ...]]:
        return {
            PipelineNode("thing-doer.1"): tuple(
                [
                    PipelineNode("data-prep.1"),
                    PipelineNode("data-prep.2"),
                    PipelineNode("data-prep.3"),
                ]
            ),
            PipelineNode("thing-doer.2"): tuple(
                [
                    PipelineNode("data-prep.1"),
                ]
            ),
            PipelineNode("thing-doer.3"): tuple(
                [
                    PipelineNode("data-prep.3"),
                ]
            ),
            PipelineNode("thing-doer.4"): tuple(
                [
                    PipelineNode("data-prep.1"),
                    PipelineNode("data-prep.3"),
                ]
            ),
            PipelineNode("result-eval.1"): tuple(
                [
                    PipelineNode("thing-doer.1"),
                    PipelineNode("thing-doer.2"),
                    PipelineNode("thing-doer.3"),
                    PipelineNode("thing-doer.4"),
                ]
            ),
        }
