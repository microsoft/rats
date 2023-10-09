from oneml.processors.dag import DagSubmitter, INodeExecutableFactory
from oneml.processors.io import (
    IGetReadServicesForType,
    IGetWriteServicesForType,
    IReadFromUriPipelineBuilder,
    IRegisterReadServiceForType,
    IRegisterWriteServiceForType,
    IWriteToNodeBasedUriPipelineBuilder,
    IWriteToRelativePathPipelineBuilder,
    IWriteToUriPipelineBuilder,
    PluginRegisterReadersAndWriters,
)
from oneml.processors.training import IPersistFittedEvalPipeline
from oneml.processors.ux import PipelineRunnerFactory
from oneml.services import ContextId, ServiceId, scoped_context_ids, scoped_service_ids

from ._config import ParametersForTaskService
from ._hydra import HydraContext, PipelineConfigService


@scoped_service_ids
class OnemlProcessorsServices:
    # Things are grouped by making the service id name match
    # We create multiple entries here if we want to change the type (but not the id)
    REGISTER_TYPE_READER = ServiceId[IRegisterReadServiceForType]("type-to-read-service-mapper")
    GET_TYPE_READER = ServiceId[IGetReadServicesForType]("type-to-read-service-mapper")

    REGISTER_TYPE_WRITER = ServiceId[IRegisterWriteServiceForType]("type-to-write-service-mapper")
    GET_TYPE_WRITER = ServiceId[IGetWriteServicesForType]("type-to-write-service-mapper")

    READ_FROM_URI_PIPELINE_BUILDER = ServiceId[IReadFromUriPipelineBuilder](
        "read-from-uri-pipeline-builder"
    )
    WRITE_TO_URI_PIPELINE_BUILDER = ServiceId[IWriteToUriPipelineBuilder](
        "write-to-uri-pipeline-builder"
    )
    WRITE_TO_RELATIVE_PATH_PIPELINE_BUILDER = ServiceId[IWriteToRelativePathPipelineBuilder](
        "write-to-relative-path-pipeline-builder"
    )
    WRITE_TO_NODE_BASED_URI_PIPELINE_BUILDER = ServiceId[IWriteToNodeBasedUriPipelineBuilder](
        "write-to-node-based-uri-pipeline-builder"
    )
    NODE_EXECUTABLE_FACTORY = ServiceId[INodeExecutableFactory]("node-executable-factory")
    DAG_SUBMITTER = ServiceId[DagSubmitter]("dag-submitter")
    PIPELINE_RUNNER_FACTORY = ServiceId[PipelineRunnerFactory]("pipeline-runner-factory")
    PERSIST_FITTED_EVAL_PIPELINE = ServiceId[IPersistFittedEvalPipeline](
        "persist-fitted-eval-pipeline"
    )
    PLUGIN_REGISTER_READERS_AND_WRITERS = ServiceId[PluginRegisterReadersAndWriters](
        "plugin-register-readers-and-writers"
    )
    PIPELINE_CONFIG_SERVICE = ServiceId[PipelineConfigService]("pipeline-config-service")
    PARAMETERS_FOR_TASK_SERVICE = ServiceId[ParametersForTaskService](
        "parameters-for-task-service"
    )


@scoped_service_ids
class OnemlProcessorServiceGroups:
    pass


@scoped_context_ids
class OnemlProcessorsContexts:
    HYDRA = ContextId[HydraContext]("hydra")
