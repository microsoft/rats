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
    ServiceProvider,
    container,
)
from ._executables import App, Executable
from ._ids import ServiceId, T_ExecutableType, T_ServiceType
from ._mains import make_main, run_main
from ._namespaces import ProviderNamespaces
from ._plugin_container import PluginContainers
from ._runtimes import NullRuntime, Runtime
from ._scoping import autoscope
from ._simple_apps import AppServices, SimpleApplication, StandardRuntime
from ._static_container import StaticContainer, StaticProvider

__all__ = [
    "App",
    "AppBundle",
    "AppContainer",
    "AppPlugin",
    "AppServices",
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
    "ServiceProvider",
    "SimpleApplication",
    "StandardRuntime",
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
    "make_main",
    "run_main",
    "service",
]
