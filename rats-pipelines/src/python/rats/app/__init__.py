"""Main application package for rats."""

from ._io2_di_container import RatsIo2Services
from ._rats_app import RatsApp
from ._rats_app_plugins import AppPlugin, RatsAppNoopPlugin
from ._rats_app_services import RatsAppGroups, RatsAppServices
from ._session_services import RatsSessionExecutables
from ._ux import pipeline, scoped_pipeline_ids

__all__ = [
    # _rats_app_plugins
    "AppPlugin",
    # _rats_app
    "RatsApp",
    # _rats_app_services
    "RatsAppGroups",
    "RatsAppNoopPlugin",
    "RatsAppServices",
    # _io2_di_container
    "RatsIo2Services",
    # _session_services
    "RatsSessionExecutables",
    # _ux
    "pipeline",
    "scoped_pipeline_ids",
]
