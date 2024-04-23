from ._legacy_services_wrapper import Services as LegacyWrapperServices
from ._pipeline_registry import Groups as PipelineRegistryGroups
from ._pipeline_registry import Services as PipelineRegistryServices


class Groups:
    EXECUTABLE_PIPELINES = PipelineRegistryGroups.EXECUTABLE_PIPELINES


class Services:
    PIPELINE_RUNNER_FACTORY = LegacyWrapperServices.PIPELINE_RUNNER_FACTORY
    PIPELINE_TO_DOT = LegacyWrapperServices.PIPELINE_TO_DOT
    EXECUTABLE_PIPELINES_REGISTRY = PipelineRegistryServices.EXECUTABLE_PIPELINES_REGISTRY

    Groups = Groups
