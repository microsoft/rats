from abc import abstractmethod
from typing import Protocol

from oneml.pipelines.dag import PipelineNode
from oneml.pipelines.session import (
    CallableExecutable,
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
    def add_executable(
        self, node: PipelineNode, session_executable: IPipelineSessionExecutable
    ) -> None:
        pass


class ExecutablesPlugin(IPipelineSessionPlugin):

    _node: PipelineNode
    _session_executable: IPipelineSessionExecutable

    def __init__(self, node: PipelineNode, session_executable: IPipelineSessionExecutable) -> None:
        self._node = node
        self._session_executable = session_executable

    def on_session_init(self, session_client: PipelineSessionClient) -> None:
        client = session_client.node_executables_client()
        client.register_node_executable(
            self._node,
            CallableExecutable(lambda: self._session_executable.execute(session_client)),
        )


class PipelineBuilderExecutablesClient(IManageBuilderExecutables):

    _session_plugin_client: IRegisterPipelineSessionPlugins

    def __init__(self, session_plugin_client: IRegisterPipelineSessionPlugins) -> None:
        self._session_plugin_client = session_plugin_client

    def add_executable(
        self, node: PipelineNode, session_executable: IPipelineSessionExecutable
    ) -> None:

        self._session_plugin_client.register_plugin(
            ExecutablesPlugin(
                node=node,
                session_executable=session_executable,
            )
        )
