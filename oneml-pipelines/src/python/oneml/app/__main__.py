import uuid

from oneml.app import OnemlApp, OnemlAppServices
from oneml.pipelines.building import PipelineBuilderFactory
from oneml.pipelines.session import IExecutable
from oneml.pipelines.session._session_client import PipelineSessionClient


class ExamplePipeline(IExecutable):

    _builder_factory: PipelineBuilderFactory

    def __init__(
        self,
        builder_factory: PipelineBuilderFactory,
    ) -> None:
        self._builder_factory = builder_factory

    def execute(self) -> None:
        rnd = str(uuid.uuid4())
        print(f"hello world: {rnd}")

    def create_pipeline_session(self) -> PipelineSessionClient:
        builder = self._builder_factory.get_instance()
        builder.add_node(builder.node("a"))
        builder.add_node(builder.node("b"))
        builder.add_executable(builder.node("a"), self)
        builder.add_executable(builder.node("b"), self)
        builder.add_dependency(builder.node("b"), builder.node("a"))
        return builder.build_session()


app = OnemlApp.default()
example = ExamplePipeline(
    builder_factory=app.get_service(OnemlAppServices.PIPELINE_BUILDER_FACTORY),
)

pipeline_registry = app.get_service(OnemlAppServices.PIPELINE_REGISTRY)
pipeline_registry.register_pipeline_provider("hello-world", example.create_pipeline_session)

app.execute_pipeline("hello-world")
# app.execute_pipeline("hello-world")
