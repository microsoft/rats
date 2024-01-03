from collections.abc import Callable
from typing import Any

from oneml.app_api import InitializePluginsExe
from oneml.pipelines.building import PipelineBuilderClient
from oneml.pipelines.dag import IManagePipelineDags
from oneml.services import (
    ContextClient,
    ExecutablesClient,
    IExecutable,
    IManageServices,
    IProvideServices,
    ServiceId,
    scoped_service_ids,
)

from ._oneml_app_plugins import AppPlugin


@scoped_service_ids
class PrivateOnemlAppServiceGroups:
    APP_PLUGINS = ServiceId[AppPlugin]("app-plugins")
    IO_REGISTRY_PLUGINS = ServiceId[Callable[[], None]]("io-registry-plugins")


@scoped_service_ids
class OnemlAppServices:
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
class OnemlAppGroups:
    PIPELINE_CONTAINER = ServiceId[Any]("pipeline-container")
