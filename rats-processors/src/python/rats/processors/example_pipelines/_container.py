from rats import apps

from ._complex_pipeline import ExampleComplexPipelineBuilder
from ._lr_pipeline_container import LRPipelineContainer
from ._simple_typed_pipeline import ExampleSimpleTypedPipelineBuilder
from ._simple_untyped_pipeline import ExampleSimpleUntypedPipelineBuilder


class ExamplePipelinesContainer(apps.AnnotatedContainer):
    @apps.container()
    def example_pipeline1(self) -> ExampleSimpleUntypedPipelineBuilder:
        return ExampleSimpleUntypedPipelineBuilder()

    @apps.container()
    def example_pipeline2(self) -> ExampleSimpleTypedPipelineBuilder:
        return ExampleSimpleTypedPipelineBuilder()

    @apps.container()
    def example_pipeline3(self) -> ExampleComplexPipelineBuilder:
        return ExampleComplexPipelineBuilder(app=self)

    @apps.container()
    def lr_pipeline_container(self) -> LRPipelineContainer:
        return LRPipelineContainer()
