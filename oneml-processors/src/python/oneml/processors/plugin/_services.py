from oneml.services import ServiceId, scoped_service_ids

from ..dag import PipelineSessionProvider
from ..ux import PipelineRunnerFactory


@scoped_service_ids
class OnemlProcessorsServices:
    PIPELINE_SESSION_PROVIDER = ServiceId[PipelineSessionProvider]("pipeline-session-provider")
    PIPELINE_RUNNER_FACTORY = ServiceId[PipelineRunnerFactory]("pipeline-runner-factory")


@scoped_service_ids
class OnemlProcessorsServiceGroups:
    pass
