from oneml.app import OnemlApp, OnemlAppServices
from oneml.pipelines.session import PipelineSessionClient
from oneml.processors import PipelineBuilder, PipelineSessionProvider
from oneml.processors.example._processors import A, B, C, D
from oneml.processors.services import OnemlProcessorsServices


class ExamplePipeline:
    _session_provider: PipelineSessionProvider

    def __init__(self, session_provider: PipelineSessionProvider) -> None:
        self._session_provider = session_provider

    def get(self) -> PipelineSessionClient:
        a = PipelineBuilder.task(A, "A")
        b = PipelineBuilder.task(B, "B")
        c = PipelineBuilder.task(C, "C")
        d = PipelineBuilder.task(D, "D")

        diamond = PipelineBuilder.combine(
            pipelines=[a, b, c, d],
            dependencies=(
                b.inputs.x << a.outputs.z1,
                c.inputs.x << a.outputs.z2,
                d.inputs.x1 << b.outputs.z,
                d.inputs.x2 << c.outputs.z,
            ),
            name="diamond",
        )

        return self._session_provider.get_session(diamond._dag)


app = OnemlApp.default()
example = ExamplePipeline(
    session_provider=app.get_service(OnemlProcessorsServices.PIPELINE_SESSION_PROVIDER),
)
pipeline_registry = app.get_service(OnemlAppServices.PIPELINE_REGISTRY)
pipeline_registry.register_pipeline_provider("diamond-example", example.get)

app.execute_pipeline("diamond-example")
