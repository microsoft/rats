from oneml.pipelines.session import (
    PipelineNodeExecutablesClient,
    PipelineNodeStateClient,
    PipelineSessionClient,
    PipelineSessionFrameClient,
    PipelineSessionStateClient,
)
from oneml.services import ServiceId, scoped_service_ids


@scoped_service_ids
class OnemlSessionServices:
    """
    This services class should stay private! Anything we want to expose should be exposed through
    the OnemlAppServices class so that users have a single thing to import.
    """

    SESSION_CLIENT = ServiceId[PipelineSessionClient]("session-client")
    SESSION_STATE_CLIENT = ServiceId[PipelineSessionStateClient]("session-state-client")
    SESSION_FRAME_CLIENT = ServiceId[PipelineSessionFrameClient]("session-frame-client")
    NODE_EXECUTABLES_CLIENT = ServiceId[PipelineNodeExecutablesClient]("node-executables-client")
    NODE_STATE_CLIENT = ServiceId[PipelineNodeStateClient]("node-state-client")
