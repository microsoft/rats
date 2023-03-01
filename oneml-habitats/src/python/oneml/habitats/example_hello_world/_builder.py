import uuid

from oneml.habitats._components import OnemlHabitatsComponents
from oneml.habitats._publishers import SinglePortPublisher
from oneml.pipelines.building import PipelineBuilderFactory
from oneml.pipelines.context._client import IProvideExecutionContexts
from oneml.pipelines.session import IExecutable, PipelineSessionClient


class HelloExecutable(IExecutable):
    _output_presenter: SinglePortPublisher[str]
    _session_context: IProvideExecutionContexts[PipelineSessionClient]

    def __init__(
        self,
        output_presenter: SinglePortPublisher[str],
        session_context: IProvideExecutionContexts[PipelineSessionClient],
    ) -> None:
        self._output_presenter = output_presenter
        self._session_context = session_context

    def execute(self) -> None:
        rnd = str(uuid.uuid4())
        session = self._session_context.get_context()
        node_publisher = session.get_component(OnemlHabitatsComponents.NODE_PUBLISHER)
        print(node_publisher)
        self._output_presenter.publish(f"hello world! {rnd}")


class HelloWorldPipelineSession:
    _builder_factory: PipelineBuilderFactory
    _single_port_publisher: SinglePortPublisher[str]

    def __init__(
        self,
        builder_factory: PipelineBuilderFactory,
        single_port_publisher: SinglePortPublisher[str],
    ) -> None:
        self._builder_factory = builder_factory
        self._single_port_publisher = single_port_publisher

    def get_local_session(self) -> PipelineSessionClient:
        """
        An example pipeline that executes a few steps locally.
        """
        builder = self._builder_factory.get_instance()

        hello = HelloExecutable(
            output_presenter=self._single_port_publisher,
            session_context=builder._session_context(),
        )

        builder.add_node(builder.node("a"))
        builder.add_node(builder.node("b"))
        builder.add_executable(builder.node("a"), hello)
        builder.add_executable(builder.node("b"), hello)
        builder.add_dependency(builder.node("b"), builder.node("a"))
        return builder.build_session()
