from rats import apps
from rats.app import RatsApp as LegacyApp
from rats.apps import Container
from rats.pipelines_app import PipelineServiceContainer

from ._pipeline1 import ExamplePipelineContainer1
from ._pipeline2 import ExamplePipelineContainer2


class ExampleApp(apps.AnnotatedContainer):
    @apps.container()
    def pipeline_services(self) -> Container:
        return PipelineServiceContainer(legacy_app=LegacyApp.default(), app=self)

    @apps.container()
    def example_pipeline1(self) -> ExamplePipelineContainer1:
        return ExamplePipelineContainer1()

    @apps.container()
    def example_pipeline2(self) -> ExamplePipelineContainer2:
        return ExamplePipelineContainer2()
