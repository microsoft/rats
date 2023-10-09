import logging
from pathlib import Path

from oneml.app import OnemlApp, OnemlAppServices
from oneml.io import OnemlIoServices
from oneml.processors.dag import DagSubmitter, NodeExecutableFactory
from oneml.processors.io import (
    PluginRegisterReadersAndWriters,
    ReadFromUriPipelineBuilder,
    TypeToReadServiceMapper,
    TypeToWriteServiceMapper,
    WriteToNodeBasedUriPipelineBuilder,
    WriteToRelativePathPipelineBuilder,
    WriteToUriPipelineBuilder,
)
from oneml.processors.services import (
    HydraPipelineConfigServiceProvider,
    OnemlProcessorsContexts,
    OnemlProcessorsServices,
    ParametersForTaskHydraService,
    ParametersForTaskService,
    PipelineConfigService,
)
from oneml.processors.training import PersistFittedEvalPipeline
from oneml.processors.ux import PipelineRunnerFactory
from oneml.services import IProvideServices, after, service_group, service_provider

from ._register_rw import OnemlProcessorsRegisterReadersAndWriters

logger = logging.getLogger(__name__)


class OnemlProcessorsDiContainer:
    _app: OnemlApp

    def __init__(self, app: IProvideServices) -> None:
        assert isinstance(app, OnemlApp)
        self._app = app

    @service_provider(OnemlProcessorsServices.NODE_EXECUTABLE_FACTORY)
    def node_executable_factory(self) -> NodeExecutableFactory:
        return NodeExecutableFactory(
            services_provider=self._app.get_service(OnemlAppServices.SERVICE_CONTAINER),
            context_client=self._app.get_service(OnemlAppServices.APP_CONTEXT_CLIENT),
            publishers_getter=self._app.get_service(OnemlIoServices.PIPELINE_PUBLISHERS_GETTER),
            loaders_getter=self._app.get_service(OnemlIoServices.PIPELINE_LOADERS_GETTER),
        )

    @service_provider(OnemlProcessorsServices.DAG_SUBMITTER)
    def pipeline_dag_submitter(self) -> DagSubmitter:
        return DagSubmitter(
            builder=self._app.get_service(OnemlAppServices.PIPELINE_BUILDER),
            node_executable_factory=self._app.get_service(
                OnemlProcessorsServices.NODE_EXECUTABLE_FACTORY
            ),
        )

    @service_provider(OnemlProcessorsServices.PIPELINE_RUNNER_FACTORY)
    def pipeline_runner_factory(self) -> PipelineRunnerFactory:
        return PipelineRunnerFactory(
            app=self._app,
            dag_submitter=self._app.get_service(OnemlProcessorsServices.DAG_SUBMITTER),
        )

    @service_provider(OnemlProcessorsServices.REGISTER_TYPE_READER)
    def type_to_read_service_mapper(self) -> TypeToReadServiceMapper:
        return TypeToReadServiceMapper()

    @service_provider(OnemlProcessorsServices.REGISTER_TYPE_WRITER)
    def type_to_write_service_mapper(self) -> TypeToWriteServiceMapper:
        return TypeToWriteServiceMapper()

    @service_provider(OnemlProcessorsServices.READ_FROM_URI_PIPELINE_BUILDER)
    def read_from_url_pipeline_builder(self) -> ReadFromUriPipelineBuilder:
        return ReadFromUriPipelineBuilder(
            service_provider_service_id=OnemlAppServices.SERVICE_CONTAINER,
            get_read_services_for_type=self._app.get_service(
                OnemlProcessorsServices.GET_TYPE_READER
            ),
        )

    @service_provider(OnemlProcessorsServices.WRITE_TO_URI_PIPELINE_BUILDER)
    def write_to_url_pipeline_builder(self) -> WriteToUriPipelineBuilder:
        return WriteToUriPipelineBuilder(
            service_provider_service_id=OnemlAppServices.SERVICE_CONTAINER,
            get_write_services_for_type=self._app.get_service(
                OnemlProcessorsServices.GET_TYPE_WRITER
            ),
        )

    @service_provider(OnemlProcessorsServices.WRITE_TO_RELATIVE_PATH_PIPELINE_BUILDER)
    def write_to_relative_path_pipeline_builder(self) -> WriteToRelativePathPipelineBuilder:
        return WriteToRelativePathPipelineBuilder(
            write_to_uri_pipeline_builder=self._app.get_service(
                OnemlProcessorsServices.WRITE_TO_URI_PIPELINE_BUILDER
            ),
        )

    @service_provider(OnemlProcessorsServices.WRITE_TO_NODE_BASED_URI_PIPELINE_BUILDER)
    def write_to_node_based_uri_pipeline_builder(self) -> WriteToNodeBasedUriPipelineBuilder:
        return WriteToNodeBasedUriPipelineBuilder(
            write_to_uri_pipeline_builder=self._app.get_service(
                OnemlProcessorsServices.WRITE_TO_URI_PIPELINE_BUILDER
            ),
            context_provider_service_id=OnemlAppServices.APP_CONTEXT_CLIENT,
        )

    @service_provider(OnemlProcessorsServices.PERSIST_FITTED_EVAL_PIPELINE)
    def persist_fitted_eval_pipeline(self) -> PersistFittedEvalPipeline:
        return PersistFittedEvalPipeline(
            read_pb=self._app.get_service(OnemlProcessorsServices.READ_FROM_URI_PIPELINE_BUILDER),
            write_pb=self._app.get_service(
                OnemlProcessorsServices.WRITE_TO_NODE_BASED_URI_PIPELINE_BUILDER
            ),
        )

    @service_group(after(OnemlAppServices.PLUGIN_LOAD_EXE))
    def register_readers_and_writers(self) -> PluginRegisterReadersAndWriters:
        return self._app.get_service(OnemlProcessorsServices.PLUGIN_REGISTER_READERS_AND_WRITERS)

    @service_provider(OnemlProcessorsServices.PLUGIN_REGISTER_READERS_AND_WRITERS)
    def plugin_register_readers_and_writers(self) -> OnemlProcessorsRegisterReadersAndWriters:
        return OnemlProcessorsRegisterReadersAndWriters(
            readers_registry=self._app.get_service(OnemlProcessorsServices.REGISTER_TYPE_READER),
            writers_registry=self._app.get_service(OnemlProcessorsServices.REGISTER_TYPE_WRITER),
        )

    def _parameters_config_dir(self) -> str:
        return str(Path("src/resources/params").absolute())

    def _pipeline_config_service_provider(self) -> HydraPipelineConfigServiceProvider:
        context_client = self._app.get_service(OnemlAppServices.APP_CONTEXT_CLIENT)
        return HydraPipelineConfigServiceProvider(
            config_dir=self._parameters_config_dir(),
            context_provider=context_client.get_context_provider(OnemlProcessorsContexts.HYDRA),
        )

    @service_provider(OnemlProcessorsServices.PIPELINE_CONFIG_SERVICE)
    def pipeline_config_service(self) -> PipelineConfigService:
        return self._pipeline_config_service_provider()()

    @service_provider(OnemlProcessorsServices.PARAMETERS_FOR_TASK_SERVICE)
    def parameters_for_task_service(self) -> ParametersForTaskService:
        pipeline_config_provider = self._app.get_service(
            OnemlProcessorsServices.PIPELINE_CONFIG_SERVICE
        )
        return ParametersForTaskHydraService(pipeline_config_provider)
