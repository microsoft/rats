import logging

from oneml.app import AppPlugin, OnemlAppServices
from oneml.io import OnemlIoServices
from oneml.services import (
    IManageServices,
    IProvideServices,
    ServiceId,
    scoped_service_ids,
    service_provider,
)

from ._client import DagSubmitter, INodeExecutableFactory, NodeExecutableFactory

logger = logging.getLogger(__name__)


@scoped_service_ids
class _PrivateServices:
    NODE_EXECUTABLE_FACTORY = ServiceId[INodeExecutableFactory]("node-executable-factory")
    DAG_SUBMITTER = ServiceId[DagSubmitter]("dag-submitter")


class OnemlProcessorsDagDiContainer:
    _app: IProvideServices

    def __init__(self, app: IProvideServices) -> None:
        self._app = app

    @service_provider(_PrivateServices.NODE_EXECUTABLE_FACTORY)
    def node_executable_factory(self) -> NodeExecutableFactory:
        return NodeExecutableFactory(
            services_provider=self._app.get_service(OnemlAppServices.SERVICE_CONTAINER),
            context_client=self._app.get_service(OnemlAppServices.APP_CONTEXT_CLIENT),
            publishers_getter=self._app.get_service(OnemlIoServices.PIPELINE_PUBLISHERS_GETTER),
            loaders_getter=self._app.get_service(OnemlIoServices.PIPELINE_LOADERS_GETTER),
        )

    @service_provider(_PrivateServices.DAG_SUBMITTER)
    def pipeline_dag_submitter(self) -> DagSubmitter:
        return DagSubmitter(
            builder=self._app.get_service(OnemlAppServices.PIPELINE_BUILDER),
            node_executable_factory=self._app.get_service(
                OnemlProcessorsDagServices.NODE_EXECUTABLE_FACTORY
            ),
        )


class OnemlProcessorsDagPlugin(AppPlugin):
    def load_plugin(self, app: IManageServices) -> None:
        logger.debug("initializing oneml-processors-dag plugin")
        app.parse_service_container(OnemlProcessorsDagDiContainer(app))


class OnemlProcessorsDagServices:
    NODE_EXECUTABLE_FACTORY = _PrivateServices.NODE_EXECUTABLE_FACTORY
    DAG_SUBMITTER = _PrivateServices.DAG_SUBMITTER
