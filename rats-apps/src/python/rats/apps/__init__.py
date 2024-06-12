"""
Provides a small set of libraries to help create new applications.

Applications give you the ability to define a development experience to match your project's
domain.
"""

from ._annotations import (
    AnnotatedContainer,
    autoid,
    autoid_service,
    config,
    container,
    fallback_config,
    fallback_group,
    fallback_service,
    group,
    service,
)
from ._composite_container import CompositeContainer
from ._container import (
    ConfigProvider,
    Container,
    DuplicateServiceError,
    ServiceNotFoundError,
    ServiceProvider,
)
from ._executables import App, Executable
from ._ids import ConfigId, ServiceId
from ._namespaces import ProviderNamespaces
from ._plugin_container import PluginContainers
from ._plugins import PluginRunner
from ._runtimes import Runtime, SimpleRuntime, T_ExecutableType
from ._scoping import autoscope

__all__ = [
    "AnnotatedContainer",
    "App",
    "CompositeContainer",
    "ConfigId",
    "Container",
    "DuplicateServiceError",
    "Executable",
    "PluginContainers",
    "ProviderNamespaces",
    "ConfigProvider",
    "ServiceProvider",
    "ServiceId",
    "ServiceNotFoundError",
    "autoid_service",
    "autoscope",
    "config",
    "container",
    "PluginRunner",
    "fallback_config",
    "fallback_group",
    "fallback_service",
    "group",
    "autoid",
    "service",
    "T_ExecutableType",
    "Runtime",
    "SimpleRuntime",
]
