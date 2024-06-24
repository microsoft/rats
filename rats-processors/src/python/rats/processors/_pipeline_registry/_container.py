from itertools import chain

from rats import apps

from ._pipeline_registry import PipelineRegistry
from ._services import Groups, Services


class PipelineRegistryContainer(apps.Container):
    _app: apps.Container

    def __init__(self, app: apps.Container) -> None:
        self._app = app

    @apps.service(Services.EXECUTABLE_PIPELINES_REGISTRY)
    def executable_pipelines(self) -> PipelineRegistry:
        return PipelineRegistry(
            app=self._app, entries=chain(*self._app.get_group(Groups.EXECUTABLE_PIPELINES))
        )
