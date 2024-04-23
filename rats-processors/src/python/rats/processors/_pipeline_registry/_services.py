from rats import apps

from ._pipeline_registry import IPipelineRegistry, PipelineRegistryEntry


class Services:
    EXECUTABLE_PIPELINES_REGISTRY = apps.ServiceId[IPipelineRegistry](
        "executable-pipelines-registry"
    )


class Groups:
    EXECUTABLE_PIPELINES = apps.ServiceId[tuple[PipelineRegistryEntry]]("executable-pipelines")
