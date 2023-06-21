from oneml.services import ServiceId, scoped_service_ids

from ..dag import PipelineSessionProvider
from ..ux import PipelineRunnerFactory
from ._default_port_mapper import DefaultTypeLocalRWMapper


@scoped_service_ids
class OnemlProcessorsServices:
    DEFAULT_TYPE_RW_MAPPER = ServiceId[DefaultTypeLocalRWMapper]("default-type-rw-mapper")
    PIPELINE_SESSION_PROVIDER = ServiceId[PipelineSessionProvider]("pipeline-session-provider")
    PIPELINE_RUNNER_FACTORY = ServiceId[PipelineRunnerFactory]("pipeline-runner-factory")


@scoped_service_ids
class OnemlProcessorServiceGroups:
    pass
