from oneml.pipelines.building import PipelineBuilderClient
from oneml.services import ServiceId, scoped_service_ids


@scoped_service_ids
class OnemlBuildingServices:
    """
    This services class should stay private! Anything we want to expose should be exposed through
    the OnemlAppServices class so that users have a single thing to import.
    """

    PIPELINE_BUILDER_CLIENT = ServiceId[PipelineBuilderClient]("builder-client")
