from collections.abc import Mapping
from typing import Any

from rats import apps
from rats.apps import Container
from rats.processors import _types as rpt

from .._legacy_services_wrapper import Services as LegacyServices
from .._pipeline_registry import IPipelineRegistry
from .._pipeline_registry import Services as PipelineRegistryServices


class NotebookApp(apps.AnnotatedContainer):
    @apps.container()
    def processors_app_plugins(self) -> Container:
        return apps.PluginContainers(
            app=self,
            group="rats.processors_app_plugins",
        )

    def run(self, pipeline: rpt.UPipeline, inputs: Mapping[str, Any] = {}) -> Mapping[str, Any]:
        runner_factory = self.get(LegacyServices.PIPELINE_RUNNER_FACTORY)
        runner = runner_factory(pipeline)
        outputs = runner(inputs)
        return outputs

    def display(
        self, pipeline: rpt.UPipeline, include_optional: bool = True, format: str = "png"
    ) -> None:
        from IPython.display import SVG, Image, display

        if format == "png":
            display_class = Image
        elif format == "svg":
            display_class = SVG
        else:
            raise ValueError(f"Unsupported format {format}. Supported formats are png and svg.")

        pipeline_to_dot = self.get(LegacyServices.PIPELINE_TO_DOT)
        dot = pipeline_to_dot(pipeline, include_optional=include_optional)

        display(display_class(dot.create(format=format)))

    def executable_pipelines(self) -> IPipelineRegistry:
        return self.get(PipelineRegistryServices.EXECUTABLE_PIPELINES_REGISTRY)
