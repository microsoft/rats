import logging
import uuid

from oneml.app import pipeline, scoped_pipeline_ids
from oneml.pipelines.building import PipelineBuilderClient
from oneml.services import IExecutable, ServiceId, executable

logger = logging.getLogger(__name__)


@scoped_pipeline_ids
class AdocliPipelines:
    HELLO_WORLD = ServiceId[IExecutable]("hello-world")


class AdocliPipelinesClient:

    _builder: PipelineBuilderClient

    def __init__(self, builder_client: PipelineBuilderClient) -> None:
        # TODO: this current pattern requires the builder to be initialized early
        self._builder = builder_client

    @pipeline(AdocliPipelines.HELLO_WORLD)
    def hello_world(self) -> None:
        # Define some nodes
        self._builder.add_node(self._builder.node("a"))
        self._builder.add_node(self._builder.node("b"))

        # Define the executables
        self._builder.set_executable(self._builder.node("a"), executable(self._example_step))
        self._builder.set_executable(self._builder.node("b"), executable(self._example_step))

        # Define some dependencies
        self._builder.add_dependency(self._builder.node("b"), self._builder.node("a"))

    def _example_step(self) -> None:
        rnd = str(uuid.uuid4())
        print(f"hello world: {rnd}")
