from rats import apps
from rats.app import RatsApp as LegacyApp
from rats.apps import Container
from rats.pipelines_app import PipelineServiceContainer

from ._pipeline1 import ExamplePipelineContainer


class ExampleApp(apps.AnnotatedContainer):
    @apps.container()
    def pipeline_services(self) -> Container:
        return PipelineServiceContainer(legacy_app=LegacyApp.default(), app=self)

    @apps.container()
    def example3_pipeline(self) -> ExamplePipelineContainer:
        return ExamplePipelineContainer()
