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
from ._container import Container, DuplicateServiceError, ServiceNotFoundError
from ._ids import ConfigId, P_ProviderParams, ServiceId, T_ConfigType, T_ServiceType
from ._namespaces import ProviderNamespaces
from ._scoping import autoscope

__all__ = [
    "AnnotatedContainer",
    "ConfigId",
    "Container",
    "DuplicateServiceError",
    "P_ProviderParams",
    "ProviderNamespaces",
    "ServiceId",
    "ServiceNotFoundError",
    "T_ConfigType",
    "T_ServiceType",
    "autoscope",
    "config",
    "container",
    "fallback_config",
    "fallback_group",
    "fallback_service",
    "group",
    "service",
]