import logging

from rats.app import AppPlugin, RatsAppServices
from rats.io import RatsIoServices
from rats.services import (
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


class RatsProcessorsDagDiContainer:
    _app: IProvideServices

    def __init__(self, app: IProvideServices) -> None:
        self._app = app

    @service_provider(_PrivateServices.NODE_EXECUTABLE_FACTORY)
    def node_executable_factory(self) -> NodeExecutableFactory:
        return NodeExecutableFactory(
            services_provider=self._app.get_service(RatsAppServices.SERVICE_CONTAINER),
            context_client=self._app.get_service(RatsAppServices.APP_CONTEXT_CLIENT),
            publishers_getter=self._app.get_service(RatsIoServices.PIPELINE_PUBLISHERS_GETTER),
            loaders_getter=self._app.get_service(RatsIoServices.PIPELINE_LOADERS_GETTER),
        )

    @service_provider(_PrivateServices.DAG_SUBMITTER)
    def pipeline_dag_submitter(self) -> DagSubmitter:
        return DagSubmitter(
            builder=self._app.get_service(RatsAppServices.PIPELINE_BUILDER),
            node_executable_factory=self._app.get_service(
                RatsProcessorsDagServices.NODE_EXECUTABLE_FACTORY
            ),
        )


class RatsProcessorsDagPlugin(AppPlugin):
    def load_plugin(self, app: IManageServices) -> None:
        logger.debug("initializing rats-processors-dag plugin")
        app.parse_service_container(RatsProcessorsDagDiContainer(app))


class RatsProcessorsDagServices:
    NODE_EXECUTABLE_FACTORY = _PrivateServices.NODE_EXECUTABLE_FACTORY
    DAG_SUBMITTER = _PrivateServices.DAG_SUBMITTER
