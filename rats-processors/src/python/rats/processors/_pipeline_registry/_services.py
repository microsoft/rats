from rats import apps

from ._pipeline_registry import PipelineRegistry, PipelineRegistryEntry


class Services:
    EXECUTABLE_PIPELINES_REGISTRY = apps.ServiceId[PipelineRegistry](
        "executable-pipelines-registry"
    )


class Groups:
    EXECUTABLE_PIPELINES = apps.ServiceId[tuple[PipelineRegistryEntry]]("executable-pipelines")
