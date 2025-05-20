"""
Submit applications as aml jobs, sending necessary context from the driver node.

This module combines the capabilities of [rats.app_context][] and [rats.runtime][] module to allow
the execution of any registered `rats.runtime.apps` entry-point as an aml job.
"""

from ._app import AppConfigs, Application, AppServices, main
from ._configs import (
    AmlEnvironment,
    AmlIO,
    AmlJobContext,
    AmlJobDetails,
    AmlWorkspace,
)
from ._request import Request
from ._submission import submit

__all__ = [
    "AmlEnvironment",
    "AmlIO",
    "AmlJobContext",
    "AmlJobDetails",
    "AmlWorkspace",
    "AppConfigs",
    "AppServices",
    "Application",
    "Request",
    "main",
    "submit",
]
