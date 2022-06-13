import logging
from dataclasses import dataclass
from functools import lru_cache
from typing import Callable, Dict, Tuple

from ._executable import DeferredExecutable, IExecutable
from ._node_dependencies import IManagePipelineNodeDependencies, PipelineNodeDependenciesClient
from ._node_execution import (
    IExecutePipelineNodes,
    LocalPipelineNodeExecutionContext,
    PipelineNodeExecutableRegistry,
    PipelineNodeExecutionClient,
)
from ._node_state import IManagePipelineNodeState, PipelineNodeState, PipelineNodeStateClient
from ._nodes import IManagePipelineNodes, PipelineNode, PipelineNodeClient
from ._pipelines import IStopPipelines, ITickablePipeline, PipelineSession

logger = logging.getLogger(__name__)


class MlPipeline(ITickablePipeline):

    _node_client: IManagePipelineNodes
    _node_runner: IExecutePipelineNodes
    _node_state_client: IManagePipelineNodeState
    _node_dependencies_client: IManagePipelineNodeDependencies
    _pipeline_session: IStopPipelines

    def __init__(
            self,
            node_client: IManagePipelineNodes,
            node_runner: IExecutePipelineNodes,
            node_state_client: IManagePipelineNodeState,
            node_dependencies_client: IManagePipelineNodeDependencies,
            pipeline_session: IStopPipelines):
        self._node_client = node_client
        self._node_runner = node_runner
        self._node_state_client = node_state_client
        self._node_dependencies_client = node_dependencies_client
        self._pipeline_session = pipeline_session

    def tick(self):
        self._open_frame()
        self._execute_frame()  # maybe should not be blocking?
        self._close_frame()

        # On every "tick", the DAG has to be valid.
        # We could use this to force people to define dependencies for nodes before the next tick.

    def _open_frame(self) -> None:
        self._queue_registered()

    def _execute_frame(self) -> None:
        node = self._get_runnable()
        self._node_state_client.set_node_state(node, PipelineNodeState.RUNNING)
        self._node_runner.execute_node(node)
        # TODO: how do we ensure FAILED state is properly captured?
        self._node_state_client.set_node_state(node, PipelineNodeState.COMPLETED)

    def _close_frame(self) -> None:
        registered = self._node_state_client.get_nodes_by_state(PipelineNodeState.REGISTERED)
        queued = self._node_state_client.get_nodes_by_state(PipelineNodeState.QUEUED)
        running = self._node_state_client.get_nodes_by_state(PipelineNodeState.RUNNING)

        if len(registered) == 0 and len(queued) == 0 and len(running) == 0:
            logger.debug("No pending nodes remaining.")
            self._pipeline_session.stop_pipeline()

    def _queue_registered(self) -> None:
        for node in self._node_state_client.get_nodes_by_state(PipelineNodeState.REGISTERED):
            logger.debug(f"Queueing newly registered node: {node}")
            self._node_state_client.set_node_state(node, PipelineNodeState.QUEUED)

    def _get_runnable(self) -> PipelineNode:
        complete_nodes = self._node_state_client.get_nodes_by_state(PipelineNodeState.COMPLETED)
        runnable = self._node_dependencies_client.get_nodes_with_dependencies(complete_nodes)

        for node in runnable:
            node_state = self._node_state_client.get_node_state(node)
            if node_state == PipelineNodeState.QUEUED:
                return node
            logger.debug(f"Skipping node because of state: {node_state}")

        raise RuntimeError("No runnable node found!")


@dataclass(frozen=True)
class MlPipelineConfig:
    dependencies_provider: Callable[[], Dict[PipelineNode, Tuple[PipelineNode, ...]]]
    executables_provider: Callable[[], Dict[PipelineNode, Callable[[], IExecutable]]]
    session_provider: Callable[[], PipelineSession]

    def nodes(self) -> Tuple[PipelineNode, ...]:
        return tuple(self.executables_provider().keys())


class MlPipelineProvider:
    _pipeline_config: MlPipelineConfig

    def __init__(self, pipeline_config: MlPipelineConfig):
        self._pipeline_config = pipeline_config

    @lru_cache()
    def get_pipeline(self) -> MlPipeline:
        node_client = PipelineNodeClient()
        state_client = PipelineNodeStateClient()

        executables_registry = PipelineNodeExecutableRegistry()
        local_execution_context = LocalPipelineNodeExecutionContext(locator=executables_registry)
        # TODO: re-enable remote execution support
        # remotable_execution_context = RemotablePipelineNodeExecutionContext(
        #     local_context=local_execution_context)

        executor_manager = PipelineNodeExecutionClient(
            execution_context=local_execution_context,
            registry=executables_registry,
        )

        executables = self._pipeline_config.executables_provider()

        for node in self._pipeline_config.nodes():
            node_client.register_node(node)
            state_client.set_node_state(node, PipelineNodeState.REGISTERED)
            executable = DeferredExecutable(executables[node])
            executor_manager.register_node_executable(node, executable)

        dependencies_client = PipelineNodeDependenciesClient(node_locator=node_client)
        for node, dependencies in self._pipeline_config.dependencies_provider().items():
            dependencies_client.register_node_dependencies(node, dependencies)

        return MlPipeline(
            node_client=node_client,
            node_runner=executor_manager,
            node_state_client=state_client,
            node_dependencies_client=dependencies_client,
            pipeline_session=self._pipeline_config.session_provider(),
        )
