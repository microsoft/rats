from itertools import chain

from rats import apps
from rats.app import RatsApp as LegacyApp

from ._pipeline_registry import PipelineRegistryEntry, PipelineRegistryGroups


class PipelineServiceContainer(apps.AnnotatedContainer):
    _app: apps.Container

    def __init__(self, legacy_app: LegacyApp, app: apps.Container) -> None:
        self._app = app

    @apps.autoid_service
    def executable_pipelines(self) -> tuple[PipelineRegistryEntry, ...]:
        return tuple(chain(*self._app.get_group(PipelineRegistryGroups.EXECUTABLE_PIPELINES)))


class Services:
    EXECUTABLE_PIPELINES = apps.method_service_id(PipelineServiceContainer.executable_pipelines)
