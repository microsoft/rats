"""We try to submit executables as AML jobs."""

from ._app import AppConfigs, Application, AppServices, main

__all__ = [
    "AppServices",
    "AppConfigs",
    "Application",
    "main",
]
