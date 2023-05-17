from typing import Generic, TypeVar

from oneml.pipelines.context._client import IProvideExecutionContexts
from oneml.pipelines.dag import PipelinePort, PipelinePortDataType
from oneml.pipelines.session import PipelineSessionClient


class NodeBasedPublisher:
    _session_context: IProvideExecutionContexts[PipelineSessionClient]

    def __init__(self, session_context: IProvideExecutionContexts[PipelineSessionClient]) -> None:
        self._session_context = session_context

    def publish(
        self,
        port: PipelinePort[PipelinePortDataType],
        data: PipelinePortDataType,
    ) -> None:
        session = self._session_context.get_context()
        exe_client = session.node_executables_client()
        node = exe_client.get_active_node()
        iomanager_client = session.iomanager_client()
        data_client = iomanager_client.get_dataclient(node, port)
        data_client.publish_data(node, port, data)


T = TypeVar("T")


class SimplePublisher(Generic[T]):
    _publisher: NodeBasedPublisher

    def __init__(self, publisher: NodeBasedPublisher) -> None:
        self._publisher = publisher

    def publish(self, data: T) -> None:
        self._publisher.publish(PipelinePort[T]("__main__"), data)
