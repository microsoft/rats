from abc import abstractmethod
from typing import Protocol

from oneml.pipelines.dag import PipelineNode
from oneml.pipelines.session import (
    IExecutable,
    IPipelineSessionPlugin,
    IRegisterPipelineSessionPlugins,
    PipelineSessionClient,
)


class IPipelineSessionExecutable(Protocol):
    @abstractmethod
    def execute(self, session_client: PipelineSessionClient) -> None:
        pass


class IManageBuilderExecutables(Protocol):
    @abstractmethod
    def add_executable(self, node: PipelineNode, executable: IExecutable) -> None:
        pass


class ExecutablesPlugin(IPipelineSessionPlugin):

    _node: PipelineNode
    _executable: IExecutable

    def __init__(self, node: PipelineNode, executable: IExecutable) -> None:
        self._node = node
        self._executable = executable

    def on_session_init(self, session_client: PipelineSessionClient) -> None:
        client = session_client.node_executables_client()
        client.register_node_executable(self._node, self._executable)


class PipelineBuilderExecutablesClient(IManageBuilderExecutables):

    _session_plugin_client: IRegisterPipelineSessionPlugins

    def __init__(self, session_plugin_client: IRegisterPipelineSessionPlugins) -> None:
        self._session_plugin_client = session_plugin_client

    def add_executable(self, node: PipelineNode, executable: IExecutable) -> None:
        self._session_plugin_client.register_plugin(
            ExecutablesPlugin(node=node, executable=executable),
        )
