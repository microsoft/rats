import logging
from dataclasses import dataclass
from functools import lru_cache
from typing import Callable, Dict, Tuple

from ._close_frame_commands import ClosePipelineFrameCommand
from ._executable import DeferredExecutable, IExecutable
from ._execute_frame_commands import ExecutePipelineFrameCommand
from ._node_dependencies import PipelineNodeDependenciesClient
from ._node_execution import (
    LocalPipelineNodeExecutionContext,
    PipelineNodeExecutableRegistry,
    PipelineNodeExecutionClient,
)
from ._node_state import PipelineNodeState, PipelineNodeStateClient
from ._nodes import PipelineNode, PipelineNodeClient
from ._open_frame_commands import (
    OpenPipelineFrameCommand,
    PromoteQueuedNodesCommand,
    PromoteRegisteredNodesCommand,
)
from ._pipelines import IManagePipelines, ITickablePipeline

logger = logging.getLogger(__name__)


class MlPipeline(ITickablePipeline):

    _open_frame_command: IExecutable
    _execute_frame_command: IExecutable
    _close_frame_command: IExecutable

    def __init__(
            self,
            open_frame_command: IExecutable,
            execute_frame_command: IExecutable,
            close_frame_command: IExecutable):
        self._open_frame_command = open_frame_command
        self._execute_frame_command = execute_frame_command
        self._close_frame_command = close_frame_command

    def tick(self):
        self._open_frame_command.execute()
        self._execute_frame_command.execute()
        self._close_frame_command.execute()


@dataclass(frozen=True)
class MlPipelineConfig:
    dependencies_provider: Callable[[], Dict[PipelineNode, Tuple[PipelineNode, ...]]]
    executables_provider: Callable[[], Dict[PipelineNode, Callable[[], IExecutable]]]
    session_provider: Callable[[], IManagePipelines]

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
            open_frame_command=OpenPipelineFrameCommand(
                promote_registered_command=PromoteRegisteredNodesCommand(
                    state_client=state_client),
                promote_queued_command=PromoteQueuedNodesCommand(
                    state_client=state_client,
                    dependencies_client=dependencies_client,
                ),
            ),
            execute_frame_command=ExecutePipelineFrameCommand(
                state_client=state_client,
                runner=executor_manager,
            ),
            close_frame_command=ClosePipelineFrameCommand(
                state_client=state_client,
                pipeline_session=self._pipeline_config.session_provider(),
            ),
        )
