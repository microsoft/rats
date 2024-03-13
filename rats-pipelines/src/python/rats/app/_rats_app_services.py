from collections.abc import Callable
from typing import Any

from rats.app_api import InitializePluginsExe
from rats.pipelines.building import PipelineBuilderClient
from rats.pipelines.dag import IManagePipelineDags
from rats.services import (
    ContextClient,
    ExecutablesClient,
    IExecutable,
    IManageServices,
    IProvideServices,
    ServiceId,
    scoped_service_ids,
)

from ._rats_app_plugins import AppPlugin


@scoped_service_ids
class PrivateRatsAppServiceGroups:
    APP_PLUGINS = ServiceId[AppPlugin]("app-plugins")
    IO_REGISTRY_PLUGINS = ServiceId[Callable[[], None]]("io-registry-plugins")


@scoped_service_ids
class RatsAppServices:
    EXE_CLIENT = ServiceId[ExecutablesClient]("exe-client")
    SERVICE_MANAGER = ServiceId[IManageServices]("service-manager")
    SERVICE_FACTORY = ServiceId[IManageServices]("service-factory")
    SERVICE_CONTAINER = ServiceId[IProvideServices]("service-container")

    PLUGIN_LOAD_EXE = ServiceId[InitializePluginsExe]("plugin-load")

    PIPELINE_EXECUTABLE = ServiceId[IExecutable]("pipeline-executable")

    PIPELINE_BUILDER = ServiceId[PipelineBuilderClient]("pipeline-builder")
    PIPELINE_DAG_CLIENT = ServiceId[IManagePipelineDags]("pipeline-dag-client")

    APP_CONTEXT_CLIENT = ServiceId[ContextClient]("app-context-client")


@scoped_service_ids
class RatsAppGroups:
    PIPELINE_CONTAINER = ServiceId[Any]("pipeline-container")
