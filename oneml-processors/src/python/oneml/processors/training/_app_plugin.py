import logging

from oneml.app import AppPlugin
from oneml.processors.io import OnemlProcessorsIoServices
from oneml.services import (
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


class OnemlProcessorsTrainingDiContainer:
    _app: IProvideServices

    def __init__(self, app: IProvideServices) -> None:
        self._app = app

    @service_provider(_PrivateServices.PERSIST_FITTED_EVAL_PIPELINE)
    def persist_fitted_eval_pipeline(self) -> PersistFittedEvalPipeline:
        return PersistFittedEvalPipeline(
            read_pb=self._app.get_service(
                OnemlProcessorsIoServices.READ_FROM_URI_PIPELINE_BUILDER
            ),
            write_pb=self._app.get_service(
                OnemlProcessorsIoServices.WRITE_TO_NODE_BASED_URI_PIPELINE_BUILDER
            ),
        )


class OnemlProcessorsTrainingPlugin(AppPlugin):
    def load_plugin(self, app: IManageServices) -> None:
        logger.debug("initializing oneml-processors-training plugin")
        app.parse_service_container(OnemlProcessorsTrainingDiContainer(app))


class OnemlProcessorsTrainingServices:
    PERSIST_FITTED_EVAL_PIPELINE = _PrivateServices.PERSIST_FITTED_EVAL_PIPELINE
