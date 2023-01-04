from typing import Generic, TypeVar

from oneml.pipelines.context._client import IProvideExecutionContexts
from oneml.pipelines.dag import PipelinePort
from oneml.pipelines.session import PipelineSessionClient

T = TypeVar("T")


class SimpleDependenciesProvider:

    _session_context: IProvideExecutionContexts[PipelineSessionClient]

    def __init__(self, session_context: IProvideExecutionContexts[PipelineSessionClient]) -> None:
        self._session_context = session_context

    def data(self, port: PipelinePort[T]) -> T:
        session = self._session_context.get_context()
        exe_client = session.node_executables_client()
        node = exe_client.get_active_node()
        # TODO: make methods that return the input data and output data clients of the active node
        #       allows us to eliminate errors where we might provide the wrong node
        node_input = session.node_input_data_client_factory().get_instance(node)
        return node_input.get_data(port)


class SimpleProvider(Generic[T]):

    _provider: SimpleDependenciesProvider

    def __init__(self, provider: SimpleDependenciesProvider) -> None:
        self._provider = provider

    def data(self) -> T:
        return self._provider.data(PipelinePort[T]("__main__"))
