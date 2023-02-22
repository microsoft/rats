import uuid
from typing import Generic, TypeVar

from oneml.pipelines.building import PipelineBuilderFactory
from oneml.pipelines.context._client import IProvideExecutionContexts
from oneml.pipelines.dag import PipelinePort, PipelinePortDataType
from oneml.pipelines.session import IExecutable, PipelineSessionClient


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
        data_client = session.pipeline_data_client()
        data_client.publish_data(node, port, data)


T = TypeVar("T")


class SimplePublisher(Generic[T]):

    _publisher: NodeBasedPublisher

    def __init__(self, publisher: NodeBasedPublisher) -> None:
        self._publisher = publisher

    def publish(self, data: T) -> None:
        self._publisher.publish(PipelinePort[T]("output"), data)


class HelloExecutable(IExecutable):

    _output_presenter: SimplePublisher[str]

    def __init__(self, output_presenter: SimplePublisher[str]) -> None:
        self._output_presenter = output_presenter

    def execute(self) -> None:
        rnd = str(uuid.uuid4())
        self._output_presenter.publish(f"hello world! {rnd}")


class HelloWorldPipelineSession:

    _builder_factory: PipelineBuilderFactory
    _simple_publisher: SimplePublisher[str]

    def __init__(
        self,
        builder_factory: PipelineBuilderFactory,
        simple_publisher: SimplePublisher[str],
    ) -> None:
        self._builder_factory = builder_factory
        self._simple_publisher = simple_publisher

    def get_local_session(self) -> PipelineSessionClient:
        """
        An example pipeline that executed a few steps locally.
        """
        hello = HelloExecutable(
            output_presenter=self._simple_publisher,
        )

        builder = self._builder_factory.get_instance()
        builder.add_node(builder.node("a"))
        builder.add_node(builder.node("b"))
        builder.add_executable(builder.node("a"), hello)
        builder.add_executable(builder.node("b"), hello)
        builder.add_dependency(builder.node("b"), builder.node("a"))
        return builder.build_session()
