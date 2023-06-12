import logging

from oneml.app import OnemlApp, OnemlAppServices
from oneml.services import IProvideServices, provider

from ..dag import PipelineSessionProvider
from ..ux import PipelineRunnerFactory
from ._services import OnemlProcessorsServices

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
            builder_factory=self._app.get_service(OnemlAppServices.PIPELINE_BUILDER_FACTORY),
            pipeline_publisher=self._app.get_service(OnemlAppServices.PIPELINE_DATA_PUBLISHER),
            pipeline_loader=self._app.get_service(OnemlAppServices.PIPELINE_DATA_LOADER),
        )

    @provider(OnemlProcessorsServices.PIPELINE_RUNNER_FACTORY)
    def pipeline_runner_factor(self) -> PipelineRunnerFactory:
        return PipelineRunnerFactory(
            app=self._app, pipeline_session_provider=self.pipeline_session_provider()
        )
