"""
Libraries to help create applications with a strong focus on composability and testability.

Applications give you the ability to define a development experience to match your project's
domain.
"""

from ._annotations import (
    autoid,
    autoid_factory_service,
    autoid_service,
    factory_service,
    fallback_group,
    fallback_service,
    group,
    service,
)
from ._app_containers import AppBundle, AppContainer, AppPlugin, ContainerPlugin, PluginMixin
from ._composite_container import CompositeContainer
from ._container import (
    Container,
    DuplicateServiceError,
    GroupProvider,
    Provider,
    ServiceNotFoundError,
    container,
)
from ._executables import App, Executable
from ._ids import ServiceId, T_ExecutableType, T_ServiceType
from ._mains import run, run_plugin
from ._namespaces import ProviderNamespaces
from ._plugin_container import PluginContainers
from ._runtimes import NullRuntime, Runtime, StandardRuntime
from ._scoping import autoscope
from ._static_container import StaticContainer, StaticProvider, static_group, static_service

__all__ = [
    "App",
    "AppBundle",
    "AppContainer",
    "AppPlugin",
    "CompositeContainer",
    "Container",
    "ContainerPlugin",
    "DuplicateServiceError",
    "Executable",
    "GroupProvider",
    "NullRuntime",
    "PluginContainers",
    "PluginMixin",
    "Provider",
    "ProviderNamespaces",
    "Runtime",
    "ServiceId",
    "ServiceNotFoundError",
    "StandardRuntime",
    "StaticContainer",
    "StaticProvider",
    "T_ExecutableType",
    "T_ServiceType",
    "autoid",
    "autoid_factory_service",
    "autoid_service",
    "autoscope",
    "container",
    "factory_service",
    "fallback_group",
    "fallback_service",
    "group",
    "run",
    "run_plugin",
    "service",
    "static_group",
    "static_service",
]
