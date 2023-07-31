import logging
import uuid

from oneml.io import NodeOutputClient
from oneml.pipelines.building import PipelineBuilderClient
from oneml.pipelines.dag import PipelineDataDependency, PipelinePort
from oneml.services import IExecutable, ServiceId, executable, scoped_service_ids

logger = logging.getLogger(__name__)


@scoped_service_ids
class OnemlExamplePipelines:
    HELLO_WORLD = ServiceId[IExecutable]("hello-world")


class HelloWorldPipeline:
    _builder: PipelineBuilderClient
    _output: NodeOutputClient

    def __init__(
        self,
        builder_client: PipelineBuilderClient,
        output_client: NodeOutputClient,
    ) -> None:
        self._builder = builder_client
        self._output = output_client

    def execute(self) -> None:
        print("defining the hello-world pipeline")
        # Define some nodes
        self._builder.add_node(self._builder.node("a"))
        self._builder.add_node(self._builder.node("b"))
        self._builder.add_node(self._builder.node("c"))

        # Define the executables
        self._builder.set_executable(self._builder.node("a"), executable(self._example_step))
        self._builder.set_executable(self._builder.node("b"), executable(self._example_step))
        self._builder.set_executable(self._builder.node("c"), executable(self._another_step))

        # Define some dependencies
        self._builder.add_data_dependency(
            self._builder.node("b"),
            PipelineDataDependency(
                node=self._builder.node("a"),
                output_port=PipelinePort[str]("rnd"),
                input_port=PipelinePort[str]("rnd-input"),
            ),
        )
        self._builder.add_data_dependency(
            self._builder.node("c"),
            PipelineDataDependency(
                node=self._builder.node("b"),
                output_port=PipelinePort[str]("rnd"),
                input_port=PipelinePort[str]("rnd-input"),
            ),
        )

    def _example_step(self) -> None:
        rnd = str(uuid.uuid4())
        self._output.publish(PipelinePort[str]("rnd"), rnd)
        print(f"hello world: {rnd}")

    def _another_step(self) -> None:
        rnd = str(uuid.uuid4())
        print(f"another step: {rnd}")
