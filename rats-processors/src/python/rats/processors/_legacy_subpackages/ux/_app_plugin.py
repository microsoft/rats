import logging

from rats.app import AppPlugin, RatsApp
from rats.processors._legacy_subpackages.dag import RatsProcessorsDagServices
from rats.services import (
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


class RatsProcessorsUxDiContainer:
    _app: RatsApp

    def __init__(self, app: IProvideServices) -> None:
        assert isinstance(app, RatsApp)
        self._app = app

    @service_provider(_PrivateServices.PIPELINE_RUNNER_FACTORY)
    def pipeline_runner_factory(self) -> PipelineRunnerFactory:
        return PipelineRunnerFactory(
            app=self._app,
            dag_submitter=self._app.get_service(RatsProcessorsDagServices.DAG_SUBMITTER),
        )


class RatsProcessorsUxPlugin(AppPlugin):
    def load_plugin(self, app: IManageServices) -> None:
        logger.debug("initializing rats-processors-training plugin")
        app.parse_service_container(RatsProcessorsUxDiContainer(app))


class RatsProcessorsUxServices:
    PIPELINE_RUNNER_FACTORY = _PrivateServices.PIPELINE_RUNNER_FACTORY
