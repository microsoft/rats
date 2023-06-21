import logging
from functools import lru_cache

from oneml.app import OnemlApp, OnemlAppServices
from oneml.pipelines.session import OnemlSessionServices
from oneml.services import IProvideServices, provider

from ..dag import PipelineSessionProvider
from ..services import DefaultTypeLocalRWMapper, OnemlProcessorsServices
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

    @provider(OnemlProcessorsServices.DEFAULT_TYPE_RW_MAPPER)
    @lru_cache
    def default_type_rw_mapper(self) -> DefaultTypeLocalRWMapper:
        return DefaultTypeLocalRWMapper()
