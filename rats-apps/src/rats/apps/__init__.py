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
from ._app_containers import (
    EMPTY_APP_PLUGIN,
    EMPTY_PLUGIN,
    AppBundle,
    AppContainer,
    AppPlugin,
    CompositePlugin,
    ContainerPlugin,
    PluginMixin,
    bundle,
)
from ._composite_container import EMPTY_CONTAINER, CompositeContainer
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
from ._plugin_container import PythonEntryPointContainer
from ._runtimes import NullRuntime, Runtime, StandardRuntime
from ._scoping import autoscope
from ._static_container import StaticContainer, StaticProvider, static_group, static_service

__all__ = [
    "EMPTY_APP_PLUGIN",
    "EMPTY_CONTAINER",
    "EMPTY_PLUGIN",
    "App",
    "AppBundle",
    "AppContainer",
    "AppPlugin",
    "CompositeContainer",
    "CompositePlugin",
    "Container",
    "ContainerPlugin",
    "DuplicateServiceError",
    "Executable",
    "GroupProvider",
    "NullRuntime",
    "PluginMixin",
    "Provider",
    "ProviderNamespaces",
    "PythonEntryPointContainer",
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
    "bundle",
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
