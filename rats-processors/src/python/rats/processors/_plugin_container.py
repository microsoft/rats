from rats import apps

from ._legacy_subpackages import LegacyServicesWrapperContainer
from ._pipeline_registry import PipelineRegistryContainer
from .example_pipelines import ExamplePipelinesContainer


class PluginContainer(apps.Container):
    """rats.processors package top level container.

    Registered into rats.processors_app_plugins in pyproject.toml, and hence will be available in
    all apps that consume that plugin group.
    """

    _app: apps.Container

    def __init__(self, app: apps.Container) -> None:
        self._app = app

    @apps.container()
    def legacy_services(self) -> LegacyServicesWrapperContainer:
        return LegacyServicesWrapperContainer()

    @apps.container()
    def pipeline_registry(self) -> PipelineRegistryContainer:
        return PipelineRegistryContainer(app=self._app)

    @apps.container()
    def example_pipelines(self) -> ExamplePipelinesContainer:
        return ExamplePipelinesContainer()
