import logging
from functools import lru_cache

from oneml.app import OnemlApp, OnemlAppServices
from oneml.pipelines.session import OnemlSessionServices
from oneml.services import IProvideServices, provider

from .._training import PersistFittedEvalPipeline
from ..dag import PipelineSessionProvider
from ..io import (
    OnemlProcessorsRegisterReadersAndWriters,
    ReadFromUrlPipelineBuilder,
    TypeToReadServiceMapper,
    TypeToWriteServiceMapper,
    WriteToNodeBasedUriPipelineBuilder,
    WriteToUriPipelineBuilder,
)
from ..services import OnemlProcessorsServices
from ..ux import PipelineRunnerFactory

logger = logging.getLogger(__name__)


class OnemlProcessorsDiContainer:
    _app: OnemlApp

    def __init__(self, app: IProvideServices) -> None:
        assert isinstance(app, OnemlApp)
        self._app = app

    @provider(OnemlProcessorsServices.PIPELINE_SESSION_PROVIDER)
    def pipeline_session_provider(self) -> PipelineSessionProvider:
        return PipelineSessionProvider(
            services_provider=self._app.get_service(OnemlAppServices.SERVICE_CONTAINER),
            context_client=self._app.get_service(OnemlAppServices.APP_CONTEXT_CLIENT),
            session_client_getter=self._app.get_service(OnemlSessionServices.GET_SESSION_CLIENT),
            builder_factory=self._app.get_service(OnemlAppServices.PIPELINE_BUILDER_FACTORY),
        )

    @provider(OnemlProcessorsServices.PIPELINE_RUNNER_FACTORY)
    def pipeline_runner_factor(self) -> PipelineRunnerFactory:
        return PipelineRunnerFactory(
            app=self._app, pipeline_session_provider=self.pipeline_session_provider()
        )

    @provider(OnemlProcessorsServices.REGISTER_TYPE_READER)
    @provider(OnemlProcessorsServices.GET_TYPE_READER)
    @lru_cache
    def type_to_read_service_mapper(self) -> TypeToReadServiceMapper:
        return TypeToReadServiceMapper()

    @provider(OnemlProcessorsServices.REGISTER_TYPE_WRITER)
    @provider(OnemlProcessorsServices.GET_TYPE_WRITER)
    @lru_cache
    def type_to_write_service_mapper(self) -> TypeToWriteServiceMapper:
        return TypeToWriteServiceMapper()

    @provider(OnemlProcessorsServices.READ_FROM_URI_PIPELINE_BUILDER)
    def read_from_url_pipeline_builder(self) -> ReadFromUrlPipelineBuilder:
        return ReadFromUrlPipelineBuilder(
            service_provider_service_id=OnemlAppServices.SERVICES_REGISTRY,
            get_read_services_for_type=self._app.get_service(
                OnemlProcessorsServices.GET_TYPE_READER
            ),
        )

    @provider(OnemlProcessorsServices.WRITE_TO_URI_PIPELINE_BUILDER)
    def write_to_url_pipeline_builder(self) -> WriteToUriPipelineBuilder:
        return WriteToUriPipelineBuilder(
            service_provider_service_id=OnemlAppServices.SERVICES_REGISTRY,
            get_write_services_for_type=self._app.get_service(
                OnemlProcessorsServices.GET_TYPE_WRITER
            ),
        )

    @provider(OnemlProcessorsServices.WRITE_TO_NODE_BASED_URI_PIPELINE_BUILDER)
    def write_to_node_based_uri_pipeline_builder(self) -> WriteToNodeBasedUriPipelineBuilder:
        return WriteToNodeBasedUriPipelineBuilder(
            service_provider_service_id=OnemlAppServices.SERVICES_REGISTRY,
            context_provider_service_id=OnemlAppServices.CONTEXT_PROVIDER,
            output_base_uri=self._app.get_service(OnemlProcessorsServices.OUTPUT_BASE_URI),
            get_write_services_for_type=self._app.get_service(
                OnemlProcessorsServices.GET_TYPE_WRITER
            ),
        )

    @provider(OnemlProcessorsServices.PERSIST_FITTED_EVAL_PIPELINE)
    def persist_fitted_eval_pipeline(self) -> PersistFittedEvalPipeline:
        return PersistFittedEvalPipeline(
            read_pb=self._app.get_service(OnemlProcessorsServices.READ_FROM_URI_PIPELINE_BUILDER),
            write_pb=self._app.get_service(
                OnemlProcessorsServices.WRITE_TO_NODE_BASED_URI_PIPELINE_BUILDER
            ),
        )

    def _register_readers_and_writers(self) -> OnemlProcessorsRegisterReadersAndWriters:
        return OnemlProcessorsRegisterReadersAndWriters(
            readers_registry=self._app.get_service(OnemlProcessorsServices.REGISTER_TYPE_READER),
            writers_registry=self._app.get_service(OnemlProcessorsServices.REGISTER_TYPE_WRITER),
        )

    # How do we indicate that this has to be provided by some later layer?
    # @provider(OnemlProcessorsServices.OUTPUT_BASE_URI)
    # def output_base_uri(self) -> str:
    #     ...
