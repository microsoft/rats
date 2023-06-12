from oneml.pipelines.building import PipelineBuilderClient, PipelineBuilderFactory
from oneml.pipelines.registry._pipeline_registry import PipelineRegistry, PipelineRegistryPlugin
from oneml.pipelines.session import ServicesRegistry
from oneml.pipelines.session._session_components import PipelineSessionComponents
from oneml.services import (
    IManageServices,
    ServiceContainer,
    ServiceFactory,
    ServiceId,
    scoped_service_ids,
)
from oneml.services._context import ContextClient
from ._app_plugins import OnemlAppPlugin
from ..io._pipeline_data import IPipelineDataManager


@scoped_service_ids
class OnemlAppServices:
    SERVICE_MANAGER = ServiceId[IManageServices]("service-manager")
    SERVICE_FACTORY = ServiceId[ServiceFactory]("service-factory")
    SERVICE_CONTAINER = ServiceId[ServiceContainer]("service-container")

    # These are split so users can request a specific interface, but we resolve them to the same id
    # We can easily change ID and split these up if our di container needs to use them differently
    PIPELINE_DATA_MANAGER = ServiceId[IPipelineDataManager]("pipeline-data-manager")
    PIPELINE_DATA_PUBLISHER = ServiceId[IPipelineDataManager]("pipeline-data-manager")
    PIPELINE_DATA_LOADER = ServiceId[IPipelineDataManager]("pipeline-data-manager")

    # I think the services below this line need to be re-evaluated with the new tooling
    PIPELINE_BUILDER = ServiceId[PipelineBuilderClient]("pipeline-builder")
    # TODO: remove this and leverage services library instead to make sure this is bound to the session
    PIPELINE_BUILDER_FACTORY = ServiceId[PipelineBuilderFactory]("pipeline-builder-factory")
    PIPELINE_SESSION_COMPONENTS = ServiceId[PipelineSessionComponents]("pipeline-session-components")
    # TODO: can we remove this class once we migrate to the new library?
    SERVICES_REGISTRY = ServiceId[ServicesRegistry]("services-registry")
    PIPELINE_REGISTRY = ServiceId[PipelineRegistry]("pipeline-registry")
    APP_CONTEXT_CLIENT = ServiceId[ContextClient]("app-context-client")


@scoped_service_ids
class OnemlAppServiceGroups:
    PIPELINE_REGISTRY_PLUGINS = ServiceId[PipelineRegistryPlugin]("pipeline-registry-plugins")
    APP_PLUGINS = ServiceId[OnemlAppPlugin]("app-plugins")
