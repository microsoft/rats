from rats.pipelines.building import PipelineBuilderClient
from rats.services import ServiceId, scoped_service_ids


@scoped_service_ids
class RatsBuildingServices:
    """
    Private services for the rats app.

    This services class should stay private! Anything we want to expose should be exposed through
    the RatsAppServices class so that users have a single thing to import.
    """

    PIPELINE_BUILDER_CLIENT = ServiceId[PipelineBuilderClient]("builder-client")
