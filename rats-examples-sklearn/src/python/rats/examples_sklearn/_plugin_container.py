from rats import apps

from ._lr_pipeline_container import LRPipelineContainer


class PluginContainer(apps.AnnotatedContainer):
    """rats.processors package top level container.

    Registered into rats.processors_app_plugins in pyproject.toml, and hence will be available in
    all apps that consume that plugin group.
    """

    _app: apps.Container

    def __init__(self, app: apps.Container) -> None:
        self._app = app

    @apps.container()
    def lr_pipeline(self) -> LRPipelineContainer:
        return LRPipelineContainer()
