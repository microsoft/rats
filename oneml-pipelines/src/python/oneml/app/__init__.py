"""The oneml.app package contains the core lifecycle logic for running oneml pipelines."""
from ._io2_di_container import OnemlIo2Services
from ._oneml_app import OnemlApp
from ._oneml_app_plugins import AppPlugin, OnemlAppNoopPlugin
from ._oneml_app_services import OnemlAppGroups, OnemlAppServices
from ._session_services import OnemlSessionExecutables
from ._ux import pipeline, scoped_pipeline_ids

__all__ = [
    # _oneml_app_plugins
    "AppPlugin",
    # _oneml_app
    "OnemlApp",
    # _oneml_app_services
    "OnemlAppGroups",
    "OnemlAppNoopPlugin",
    "OnemlAppServices",
    # _io2_di_container
    "OnemlIo2Services",
    # _session_services
    "OnemlSessionExecutables",
    # _ux
    "pipeline",
    "scoped_pipeline_ids",
]
