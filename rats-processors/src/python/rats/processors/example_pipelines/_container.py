from rats import apps

from ._complex_pipeline import ExampleComplexPipelineBuilder
from ._simple_typed_pipeline import ExampleSimpleTypedPipelineBuilder
from ._simple_untyped_pipeline import ExampleSimpleUntypedPipelineBuilder


class ExamplePipelinesContainer(apps.Container):
    @apps.container()
    def example_pipeline1(self) -> ExampleSimpleUntypedPipelineBuilder:
        return ExampleSimpleUntypedPipelineBuilder()

    @apps.container()
    def example_pipeline2(self) -> ExampleSimpleTypedPipelineBuilder:
        return ExampleSimpleTypedPipelineBuilder()

    @apps.container()
    def example_pipeline3(self) -> ExampleComplexPipelineBuilder:
        return ExampleComplexPipelineBuilder(app=self)
