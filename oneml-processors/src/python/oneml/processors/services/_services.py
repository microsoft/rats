from oneml.services import ServiceId, scoped_service_ids

from .._training import IPersistFittedEvalPipeline
from ..dag import PipelineSessionProvider
from ..io import (
    IGetReadServicesForType,
    IGetWriteServicesForType,
    IReadFromUrlPipelineBuilder,
    IRegisterReadServiceForType,
    IRegisterWriteServiceForType,
    IWriteToNodeBasedUriPipelineBuilder,
    IWriteToUriPipelineBuilder,
)
from ..ux import PipelineRunnerFactory


@scoped_service_ids
class OnemlProcessorsServices:
    REGISTER_TYPE_READER = ServiceId[IRegisterReadServiceForType]("register-type-reader")
    REGISTER_TYPE_WRITER = ServiceId[IRegisterWriteServiceForType]("register-type-writer")
    GET_TYPE_READER = ServiceId[IGetReadServicesForType]("get-type-reader")
    GET_TYPE_WRITER = ServiceId[IGetWriteServicesForType]("get-type-writer")
    READ_FROM_URI_PIPELINE_BUILDER = ServiceId[IReadFromUrlPipelineBuilder](
        "read-from-uri-pipeline-builder"
    )
    WRITE_TO_URI_PIPELINE_BUILDER = ServiceId[IWriteToUriPipelineBuilder](
        "write-to-uri-pipeline-builder"
    )
    WRITE_TO_NODE_BASED_URI_PIPELINE_BUILDER = ServiceId[IWriteToNodeBasedUriPipelineBuilder](
        "write-to-node-based-uri-pipeline-builder"
    )
    PIPELINE_SESSION_PROVIDER = ServiceId[PipelineSessionProvider]("pipeline-session-provider")
    PIPELINE_RUNNER_FACTORY = ServiceId[PipelineRunnerFactory]("pipeline-runner-factory")
    PERSIST_FITTED_EVAL_PIPELINE = ServiceId[IPersistFittedEvalPipeline](
        "persist-fitted-eval-pipeline"
    )
    OUTPUT_BASE_URI = ServiceId[str]("output-base-uri")


@scoped_service_ids
class OnemlProcessorServiceGroups:
    pass
