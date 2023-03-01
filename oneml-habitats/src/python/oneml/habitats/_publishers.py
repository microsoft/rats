from typing import Generic, TypeVar

from oneml.pipelines.dag import PipelinePort, PipelinePortDataType
from oneml.pipelines.session._node_execution import PipelineNodeContext
from oneml.pipelines.session._session_client import PipelineSessionContext


class NodeBasedPublisher:
    """
    A simplified data publisher interface that publishes to the active node.
    """
    _session_context: PipelineSessionContext
    _node_context: PipelineNodeContext

    def __init__(
        self,
        session_context: PipelineSessionContext,
        node_context: PipelineNodeContext,
    ) -> None:
        self._session_context = session_context
        self._node_context = node_context

    def publish(
        self,
        port: PipelinePort[PipelinePortDataType],
        data: PipelinePortDataType,
    ) -> None:
        session = self._session_context.get_context()
        node = self._node_context.get_context()
        data_client = session.pipeline_data_client()
        data_client.publish_data(node, port, data)


T = TypeVar("T")


class SinglePortPublisher(Generic[T]):
    _publisher: NodeBasedPublisher

    def __init__(self, publisher: NodeBasedPublisher) -> None:
        self._publisher = publisher

    def publish(self, data: T) -> None:
        self._publisher.publish(PipelinePort[T]("output"), data)
