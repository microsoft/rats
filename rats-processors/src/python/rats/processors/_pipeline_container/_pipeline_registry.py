from typing import TypedDict

from rats import apps
from rats.processors import ux


class PipelineRegistryEntry(TypedDict):
    name: str
    doc: str
    service_id: apps.ServiceId[ux.UPipeline]


class PipelineRegistryGroups:
    EXECUTABLE_PIPELINES = apps.ServiceId[tuple[PipelineRegistryEntry, ...]](
        "executable-pipelines"
    )
