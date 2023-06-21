from oneml.services import ServiceId, scoped_service_ids

from ._running_session_registry import IGetSessionClient, RunningSessionRegistry
from ._session_components import PipelineSessionComponents
from ._session_data import SessionDataClient


@scoped_service_ids
class OnemlSessionServices:
    SESSION_DATA_CLIENT = ServiceId[SessionDataClient]("session-data-client")
    PIPELINE_SESSION_COMPONENTS = ServiceId[PipelineSessionComponents](
        "pipeline-session-components"
    )
    RUNNING_SESSION_REGISTRY = ServiceId[RunningSessionRegistry]("running-session-registry")
    GET_SESSION_CLIENT = ServiceId[IGetSessionClient]("running-session-registry")
