"""
Libraries to help create applications with a strong focus on composability and testability.

Applications give you the ability to define a development experience to match your project's
domain.
"""

from ._annotations import (
    autoid,
    autoid_service,
    fallback_group,
    fallback_service,
    group,
    service,
    factory_service,
    autoid_factory_service,
)
from ._composite_container import CompositeContainer
from ._container import (
    Container,
    DuplicateServiceError,
    Provider,
    ServiceNotFoundError,
    ServiceProvider,
    container,
)
from ._executables import App, Executable
from ._ids import ServiceId, T_ExecutableType, T_ServiceType
from ._namespaces import ProviderNamespaces
from ._plugin_container import PluginContainers
from ._plugins import PluginRunner
from ._runtimes import NullRuntime, Runtime
from ._scoping import autoscope
from ._simple_apps import AppServices, SimpleApplication, StandardRuntime
from ._static_container import StaticContainer, StaticProvider

__all__ = [
    "App",
    "CompositeContainer",
    "Container",
    "StaticContainer",
    "StaticProvider",
    "DuplicateServiceError",
    "Executable",
    "PluginContainers",
    "ProviderNamespaces",
    "ServiceProvider",
    "Provider",
    "ServiceId",
    "ServiceNotFoundError",
    "autoid_service",
    "autoscope",
    "container",
    "PluginRunner",
    "fallback_group",
    "fallback_service",
    "group",
    "autoid",
    "service",
    "T_ExecutableType",
    "T_ServiceType",
    "Runtime",
    "NullRuntime",
    "AppServices",
    "StandardRuntime",
    "StandardRuntime",
    "SimpleApplication",
    "factory_service",
    "autoid_factory_service",
]
