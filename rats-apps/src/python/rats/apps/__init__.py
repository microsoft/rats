"""
Provides a small set of libraries to help create new applications.

Applications give you the ability to define a development experience to match your project's
domain.
"""

from ._annotations import (
    AnnotatedContainer,
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
from ._ids import ConfigId, ServiceId
from ._namespaces import ProviderNamespaces
from ._plugin_container import PluginContainers
from ._scoping import autoscope

__all__ = [
    "AnnotatedContainer",
    "CompositeContainer",
    "ConfigId",
    "Container",
    "DuplicateServiceError",
    "PluginContainers",
    "ProviderNamespaces",
    "ServiceId",
    "ServiceNotFoundError",
    "autoscope",
    "config",
    "container",
    "fallback_config",
    "fallback_group",
    "fallback_service",
    "group",
    "service",
]
