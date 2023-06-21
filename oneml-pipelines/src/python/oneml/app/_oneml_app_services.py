from oneml.pipelines.building import PipelineBuilderClient, PipelineBuilderFactory
from oneml.pipelines.registry._pipeline_registry import PipelineRegistry, PipelineRegistryPlugin
from oneml.services import (
    IManageServices,
    IProvideServices,
    ServiceContainer,
    ServiceFactory,
    ServiceId,
    scoped_service_ids,
)
from oneml.services._context import ContextClient, ContextId

from ._app_plugins import OnemlAppPlugin
from ._structs import PipelineContext


@scoped_service_ids
class OnemlAppServices:
    SERVICE_MANAGER = ServiceId[IManageServices]("service-manager")
    SERVICE_FACTORY = ServiceId[ServiceFactory]("service-factory")
    SERVICE_CONTAINER = ServiceId[ServiceContainer]("service-container")

    # I think the services below this line need to be re-evaluated with the new tooling
    PIPELINE_BUILDER = ServiceId[PipelineBuilderClient]("pipeline-builder")
    # TODO: remove this and leverage services library instead to make sure this is bound to the session
    PIPELINE_BUILDER_FACTORY = ServiceId[PipelineBuilderFactory]("pipeline-builder-factory")
    # TODO: can we remove this class once we migrate to the new library?
    SERVICES_REGISTRY = ServiceId[IProvideServices]("services-registry")
    PIPELINE_REGISTRY = ServiceId[PipelineRegistry]("pipeline-registry")
    APP_CONTEXT_CLIENT = ServiceId[ContextClient]("app-context-client")

    PIPELINE_CONTEXT_ID = ContextId[PipelineContext]("pipeline")


@scoped_service_ids
class OnemlAppServiceGroups:
    PIPELINE_REGISTRY_PLUGINS = ServiceId[PipelineRegistryPlugin]("pipeline-registry-plugins")
    APP_PLUGINS = ServiceId[OnemlAppPlugin]("app-plugins")
