"""An early implementation of habitat apps and services."""

from ._contexts import (
    ContextClient,
    ContextId,
    ContextOpener,
    ContextProvider,
    IGetContexts,
    IManageContexts,
    T_ContextType,
)
from ._di_containers import service_group, service_provider
from ._executables import IExecutable, T_ExecutableType, after, before, executable
from ._executables_client import ExecutablesClient
from ._scopes import scoped_context_ids, scoped_service_ids
from ._service_container import ContextualServiceContainer, ServiceContainer
from ._service_factory import ServiceFactory
from ._service_managers import (
    DuplicateServiceIdError,
    IDefineServices,
    IManageServices,
    IProvideServices,
    ServiceIdNotFoundError,
    ServiceProvider,
)
from ._services import ServiceGroupProvider, ServiceId, T_ServiceType, Tco_ServiceType
from ._typed_containers import TypedServiceContainer

__all__ = [
    # _contexts
    "ContextClient",
    "ContextId",
    "ContextOpener",
    "ContextProvider",
    # _service_container
    "ContextualServiceContainer",
    # _service_managers
    "DuplicateServiceIdError",
    # _executables_container
    "ExecutablesClient",
    "IDefineServices",
    "IExecutable",
    "IGetContexts",
    "IManageContexts",
    "IManageServices",
    "IProvideServices",
    "ServiceContainer",
    # _service_factory
    "ServiceFactory",
    "ServiceGroupProvider",
    # _services
    "ServiceId",
    "ServiceIdNotFoundError",
    "ServiceProvider",
    "T_ContextType",
    "T_ExecutableType",
    "T_ServiceType",
    "Tco_ServiceType",
    # _typed_containers
    "TypedServiceContainer",
    "after",
    "before",
    # _executables
    "executable",
    # _scopes
    "scoped_context_ids",
    "scoped_service_ids",
    # ._di_containers
    "service_group",
    "service_provider",
]
