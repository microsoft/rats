# type: ignore
# flake8: noqa
from functools import lru_cache
from threading import Thread
from typing import Tuple

from oneml.lorenzo.logging import LoggingClient
from oneml.lorenzo.pipelines3._example._gui import DagSvg, DagVisualizer
from oneml.lorenzo.pipelines3._example._pause_step import PauseStep
from oneml.pipelines import (
    IExecutable,
    PipelineNode,
    PipelineNodeClient,
    PipelineNodeDependenciesClient,
    PipelineNodeStateClient,
    PipelineSession,
    PipelineSessionStateClient,
)


class Pipeline3ExampleApplication(IExecutable):

    _logging_client: LoggingClient
    _args: Tuple[str, ...]

    def __init__(self, logging_client: LoggingClient, args: Tuple[str, ...]):
        self._logging_client = logging_client
        self._args = args

    def execute(self) -> None:
        self._logging_client.configure_logging()

        Thread(target=self._run_gui).start()
        Thread(target=self._run_pipeline).start()

    def _run_gui(self) -> None:
        svg_client = DagSvg(
            node_client=self._node_client(),
            dependencies_client=self._dependencies_client(),
            node_state_client=self._node_state_client(),
        )

        viz = DagVisualizer(svg_client=svg_client)
        viz.execute()

    def _run_pipeline(self) -> None:
        self._pipeline_session().run_pipeline()

    @lru_cache()
    def _pipeline_state_client(self) -> PipelineSessionStateClient:
        return self._pipeline_session_builder()._session_state_client()

    @lru_cache()
    def _node_state_client(self) -> PipelineNodeStateClient:
        return self._pipeline_session_builder()._node_state_client()

    @lru_cache()
    def _dependencies_client(self) -> PipelineNodeDependenciesClient:
        return self._pipeline_session_builder()._node_dependencies_client()

    @lru_cache()
    def _node_client(self) -> PipelineNodeClient:
        return self._pipeline_session_builder()._node_client()

    @lru_cache()
    def _pipeline_session(self) -> PipelineSession:
        return self._pipeline_session_builder().build()

    @lru_cache()
    def _pipeline_session_builder(self):
        pipeline = PipelineSessionBuilder(namespace=PipelineNode("some.pipeline.name"))
        pipeline.add_node(
            node=PipelineNode("data-load"),
            executable=PauseStep(3),
            dependencies=tuple([]),
        )
        pipeline.add_node(
            node=PipelineNode("data-prep"),
            executable=PauseStep(3),
            dependencies=tuple([pipeline.node(PipelineNode("data-load"))]),
        )

        hpo = pipeline.create_namespace(
            node=PipelineNode("hpo"),
            # Do we need deps on a namespace?
            dependencies=tuple([]),
        )

        hpo.add_node(
            node=PipelineNode("train"),
            executable=PauseStep(3),
            dependencies=tuple([pipeline.node(PipelineNode("data-prep"))]),
        )

        hpo.add_node(
            node=PipelineNode("eval"),
            executable=PauseStep(3),
            dependencies=tuple(
                [
                    pipeline.node(PipelineNode("data-prep")),
                    hpo.node(PipelineNode("train")),
                ]
            ),
        )

        fold = PipelineFolds[int](range(5), hpo)
        fold.add_node(
            node=PipelineNode("foo"),
            provider=FakeFoldExecutableProvider(),
            dependencies=tuple(
                [
                    hpo.node(PipelineNode("eval")),
                ]
            ),
        )

        pipeline.add_node(
            node=PipelineNode("foo-1"),
            executable=PauseStep(3),
            dependencies=tuple([pipeline.node(PipelineNode("hpo"))]),
        )
        pipeline.add_node(
            node=PipelineNode("foo-2"),
            executable=PauseStep(3),
            dependencies=tuple([pipeline.node(PipelineNode("foo-1"))]),
        )
        pipeline.add_node(
            node=PipelineNode("foo-3"),
            executable=PauseStep(3),
            dependencies=tuple([pipeline.node(PipelineNode("foo-2"))]),
        )
        pipeline.add_node(
            node=PipelineNode("foo-4"),
            executable=PauseStep(3),
            dependencies=tuple([pipeline.node(PipelineNode("foo-3"))]),
        )
        pipeline.add_node(
            node=PipelineNode("foo-5"),
            executable=PauseStep(3),
            dependencies=tuple([pipeline.node(PipelineNode("foo-4"))]),
        )
        pipeline.add_node(
            node=PipelineNode("foo-6"),
            executable=PauseStep(3),
            dependencies=tuple([pipeline.node(PipelineNode("foo-5"))]),
        )

        return pipeline
