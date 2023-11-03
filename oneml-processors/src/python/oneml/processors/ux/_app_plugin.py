import logging

from oneml.app import AppPlugin, OnemlApp
from oneml.processors.dag import OnemlProcessorsDagServices
from oneml.services import (
    IManageServices,
    IProvideServices,
    ServiceId,
    scoped_service_ids,
    service_provider,
)

from ._session import PipelineRunnerFactory

logger = logging.getLogger(__name__)


@scoped_service_ids
class _PrivateServices:
    PIPELINE_RUNNER_FACTORY = ServiceId[PipelineRunnerFactory]("pipeline-runner-factory")


class OnemlProcessorsUxDiContainer:
    _app: OnemlApp

    def __init__(self, app: IProvideServices) -> None:
        assert isinstance(app, OnemlApp)
        self._app = app

    @service_provider(_PrivateServices.PIPELINE_RUNNER_FACTORY)
    def pipeline_runner_factory(self) -> PipelineRunnerFactory:
        return PipelineRunnerFactory(
            app=self._app,
            dag_submitter=self._app.get_service(OnemlProcessorsDagServices.DAG_SUBMITTER),
        )


class OnemlProcessorsUxPlugin(AppPlugin):
    def load_plugin(self, app: IManageServices) -> None:
        logger.debug("initializing oneml-processors-training plugin")
        app.parse_service_container(OnemlProcessorsUxDiContainer(app))


class OnemlProcessorsUxServices:
    PIPELINE_RUNNER_FACTORY = _PrivateServices.PIPELINE_RUNNER_FACTORY
