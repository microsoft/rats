from typing import Any, Callable

from oneml.app_api import InitializePluginsExe
from oneml.pipelines.building import PipelineBuilderClient
from oneml.pipelines.dag import IManagePipelineDags
from oneml.pipelines.session import PipelineNodeExecutablesClient
from oneml.services import (
    IExecutable,
    IGetContexts,
    IManageServices,
    IProvideServices,
    ServiceId,
    scoped_service_ids,
)

from ._oneml_app_plugins import AppPlugin


@scoped_service_ids
class PrivateOnemlAppServices:
    """
    The Service IDs of services we do not want to expose to external users of this package.

    In order to keep these services private, we must never expose this class in __init__.py. The
    providers for these services can still be mixed into any DI Container without worry of it
    being exposed, but the DI Container must be in the same package as this class.

    It's worth noting that we, as a Oneml Application, can decide to hide services in the registry
    that might actually be public classes. This is not about the publicity of the class,
    but whether we want the user to be able to retrieve the instance of this class from our
    service containers (App).
    """

    PARENT_NODE_EXE_CLIENT = ServiceId[PipelineNodeExecutablesClient]("parent-node-exe-client")


@scoped_service_ids
class PrivateOnemlAppServiceGroups:
    APP_PLUGINS = ServiceId[AppPlugin]("app-plugins")
    IO_REGISTRY_PLUGINS = ServiceId[Callable[[], None]]("io-registry-plugins")


@scoped_service_ids
class OnemlAppServices:
    SERVICE_MANAGER = ServiceId[IManageServices]("service-manager")
    SERVICE_FACTORY = ServiceId[IManageServices]("service-factory")
    SERVICE_CONTAINER = ServiceId[IProvideServices]("service-container")

    PLUGIN_LOAD_EXE = ServiceId[InitializePluginsExe]("plugin-load")

    PIPELINE_EXECUTABLE = ServiceId[IExecutable]("pipeline-executable")

    PIPELINE_BUILDER = ServiceId[PipelineBuilderClient]("pipeline-builder")
    PIPELINE_DAG_CLIENT = ServiceId[IManagePipelineDags]("pipeline-dag-client")

    APP_CONTEXT_CLIENT = ServiceId[IGetContexts]("app-context-client")


@scoped_service_ids
class OnemlAppGroups:
    PIPELINE_CONTAINER = ServiceId[Any]("pipeline-container")
