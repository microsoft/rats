from __future__ import annotations

import logging
from abc import abstractmethod
from typing import Dict, Protocol

from ._executable import IExecutable
from ._nodes import PipelineNode

logger = logging.getLogger(__name__)


class IExecutePipelineNodes(Protocol):
    @abstractmethod
    def execute_node(self, node: PipelineNode) -> None:
        """
        """


class ILocatePipelineNodeExecutables(Protocol):
    @abstractmethod
    def get_node_executable(self, node: PipelineNode) -> IExecutable:
        """
        """


class IRegisterPipelineNodeExecutables(Protocol):
    @abstractmethod
    def register_node_executable(self, node: PipelineNode, executable: IExecutable) -> None:
        """
        """


class IRegisterRemotePipelineNodes(Protocol):
    @abstractmethod
    def register_remote_node(self, node: PipelineNode) -> None:
        """
        """


class LocalPipelineNodeExecutionContext(IExecutePipelineNodes):

    _locator: ILocatePipelineNodeExecutables

    def __init__(self, locator: ILocatePipelineNodeExecutables):
        self._locator = locator

    def execute_node(self, node: PipelineNode) -> None:
        self._locator.get_node_executable(node).execute()


class PipelineNodeExecutableRegistry(
        ILocatePipelineNodeExecutables, IRegisterPipelineNodeExecutables):

    _executables: Dict[PipelineNode, IExecutable]

    def __init__(self) -> None:
        self._executables = {}

    def register_node_executable(self, node: PipelineNode, executable: IExecutable) -> None:
        if node in self._executables:
            raise RuntimeError(f"Executable already registered for node: {node}")

        self._executables[node] = executable

    def get_node_executable(self, node: PipelineNode) -> IExecutable:
        if node not in self._executables:
            raise RuntimeError(f"No executable registered for node: {node}")

        return self._executables[node]


class PipelineNodeExecutionClient(
        IExecutePipelineNodes,
        IRegisterPipelineNodeExecutables):

    _execution_context: IExecutePipelineNodes
    _registry: PipelineNodeExecutableRegistry

    def __init__(
            self,
            execution_context: IExecutePipelineNodes,
            registry: PipelineNodeExecutableRegistry):

        self._execution_context = execution_context
        self._registry = registry

    def register_node_executable(self, node: PipelineNode, executable: IExecutable) -> None:
        self._registry.register_node_executable(node, executable)

    def execute_node(self, node: PipelineNode) -> None:
        self._execution_context.execute_node(node)

    def get_node_executable(self, node: PipelineNode) -> IExecutable:
        return self._registry.get_node_executable(node)

#
# class RemotablePipelineNodeExecutionContext(
#         IExecutePipelineNodes, IRegisterRemotePipelineNodes):
#
#     _remote_nodes: Set[PipelineNode]
#
#     _local_context: IExecutePipelineNodes
#
#     def __init__(self, local_context: IExecutePipelineNodes):
#         self._remote_nodes = set()
#
#         self._local_context = local_context
#
#     def execute_node(self, node: PipelineNode) -> None:
#         if self._node_should_run_remotely(node):
#             self._execute_remotely(node)
#         else:
#             self._local_context.execute_node(node)
#
#     def register_remote_node(self, node: PipelineNode) -> None:
#         if node in self._remote_nodes:
#             raise RuntimeError(f"Remote node already registered: {node}")
#
#         self._remote_nodes.add(node)
#
#     def _node_should_run_remotely(self, node: PipelineNode) -> bool:
#         if node not in self._remote_nodes:
#             return False
#
#         if self._remote_node_env_key(node) in os.environ.keys():
#             logger.debug(f"Detected remote execution for node: {node.key}")
#             return False
#
#         return True
#
#     def _execute_remotely(self, node: PipelineNode) -> None:
#         logger.debug(f"Executing node remotely: {node}")
#
#         exe = sys.executable
#         args = list(sys.argv)
#         env = dict(os.environ)
#         command = [exe, *args]
#         env[self._remote_node_env_key(node)] = "1"
#         # TODO: Where do I check this to ensure no other nodes run in this process?
#         #       I think it has to happen in _node_state.py.
#         #       Do we need to remove the coupling to Dependencies?
#         #       Or we can use Dependencies to represent remote nodes as two nodes.
#         #       remote-a depends on remote-a1
#         #       remote-a1 depends on nothing and launches sub-process
#         #       remote-a does not depend on remote-a1 in sub-process, so runs
#         #       sub-process ends and remote-a1 marks the remote-a node COMPLETED
#         # TODO: How do we manage the data if a remote node depends on a locally run one?
#         #       We don't need data access in the execution layer.
#         #       We just need to communicate the state of the DAG within the `tick`.
#         # TODO: How do we handle conflicts between many nested DAG runs?
#         #       I think we need to give sessions IDs.
#         #       We can make all session data available in a file.
#         #       The session data can contain things like the node states.
#         #       This allows us to only use one environment variable per DAG session.
#         env["ONEML_PIPELINE_REMOTE_EXECUTION"] = "1"
#         logger.debug(f"Running command: {' '.join(command)}")
#         logger.debug(f"Running command with env: ONEML_PIPELINE_REMOTE_NODE_{node.key}")
#
#         subprocess.run(command, env=env)
#
#     def _remote_node_env_key(self, node: PipelineNode) -> str:
#         return f"ONEML_PIPELINE_REMOTE_NODE_{node.key}"
