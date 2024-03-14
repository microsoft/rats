from rats.pipelines.session import (
    PipelineNodeExecutablesClient,
    PipelineNodeStateClient,
    PipelineSessionClient,
    PipelineSessionFrameClient,
    PipelineSessionStateClient,
)
from rats.services import ServiceId, scoped_service_ids


@scoped_service_ids
class RatsSessionServices:
    """
    Rats session services.

    This services class should stay private! Anything we want to expose should be exposed through
    the RatsAppServices class so that users have a single thing to import.
    """

    SESSION_CLIENT = ServiceId[PipelineSessionClient]("session-client")
    SESSION_STATE_CLIENT = ServiceId[PipelineSessionStateClient]("session-state-client")
    NODE_EXECUTABLES_CLIENT = ServiceId[PipelineNodeExecutablesClient]("node-executables-client")
    NODE_STATE_CLIENT = ServiceId[PipelineNodeStateClient]("node-state-client")


@scoped_service_ids
class RatsSessionExecutables:
    """
    Rats session executables.

    Sessions are made up of executions of frames; some of which, execute nodes. The services
    below allow us to attach hooks using `before()` and `after()`.

    Example:
        from rats.services import executable, service_provider, before
        class MyDiContainer:
            @service_provider(before(RatsSessionExecutables.FRAME))
            def frame_logger(self) -> IExecutable:
                   return executable(lambda: print("frame is about to execute"))
    """

    FRAME = ServiceId[PipelineSessionFrameClient]("frame")
    NODE = ServiceId[PipelineNodeExecutablesClient]("node")
