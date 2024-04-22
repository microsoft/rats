from rats import apps
from rats.app import RatsApp as LegacyApp
from rats.apps import Container
from rats.pipelines_app import PipelineServiceContainer

from ._complex_pipeline import ExampleComplexPipelineBuilder
from ._simple_typed_pipeline import ExampleSimpleTypedPipelineBuilder
from ._simple_untyped_pipeline import ExampleSimpleUntypedPipelineBuilder


class ExampleApp(apps.AnnotatedContainer):
    @apps.container()
    def pipeline_services(self) -> Container:
        return PipelineServiceContainer(legacy_app=LegacyApp.default(), app=self)

    @apps.container()
    def example_pipeline1(self) -> ExampleSimpleUntypedPipelineBuilder:
        return ExampleSimpleUntypedPipelineBuilder()

    @apps.container()
    def example_pipeline2(self) -> ExampleSimpleTypedPipelineBuilder:
        return ExampleSimpleTypedPipelineBuilder()

    @apps.container()
    def example_pipeline3(self) -> ExampleComplexPipelineBuilder:
        return ExampleComplexPipelineBuilder(app=self)
