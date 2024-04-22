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
from ._container import Container, DuplicateServiceError, ServiceNotFoundError
from ._executables import App, AppContainer, Executable
from ._ids import ConfigId, ServiceId
from ._namespaces import ProviderNamespaces
from ._plugin_container import PluginContainers
from ._scoping import autoscope

__all__ = [
    "AnnotatedContainer",
    "App",
    "AppContainer",
    "CompositeContainer",
    "ConfigId",
    "Container",
    "DuplicateServiceError",
    "Executable",
    "PluginContainers",
    "ProviderNamespaces",
    "ServiceId",
    "ServiceNotFoundError",
    "autoid_service",
    "autoscope",
    "config",
    "container",
    "fallback_config",
    "fallback_group",
    "fallback_service",
    "group",
    "autoid",
    "service",
]
