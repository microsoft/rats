import logging

from rats.app import AppPlugin
from rats.processors._legacy_subpackages.io import RatsProcessorsIoServices
from rats.services import (
    IManageServices,
    IProvideServices,
    ServiceId,
    scoped_service_ids,
    service_provider,
)

from ._persist_fitted import IPersistFittedEvalPipeline, PersistFittedEvalPipeline

logger = logging.getLogger(__name__)


@scoped_service_ids
class _PrivateServices:
    PERSIST_FITTED_EVAL_PIPELINE = ServiceId[IPersistFittedEvalPipeline](
        "persist-fitted-eval-pipeline"
    )


class RatsProcessorsTrainingDiContainer:
    _app: IProvideServices

    def __init__(self, app: IProvideServices) -> None:
        self._app = app

    @service_provider(_PrivateServices.PERSIST_FITTED_EVAL_PIPELINE)
    def persist_fitted_eval_pipeline(self) -> PersistFittedEvalPipeline:
        return PersistFittedEvalPipeline(
            read_pb=self._app.get_service(RatsProcessorsIoServices.READ_FROM_URI_PIPELINE_BUILDER),
            write_pb=self._app.get_service(
                RatsProcessorsIoServices.WRITE_TO_NODE_BASED_URI_PIPELINE_BUILDER
            ),
        )


class RatsProcessorsTrainingPlugin(AppPlugin):
    def load_plugin(self, app: IManageServices) -> None:
        logger.debug("initializing rats-processors-training plugin")
        app.parse_service_container(RatsProcessorsTrainingDiContainer(app))


class RatsProcessorsTrainingServices:
    PERSIST_FITTED_EVAL_PIPELINE = _PrivateServices.PERSIST_FITTED_EVAL_PIPELINE
