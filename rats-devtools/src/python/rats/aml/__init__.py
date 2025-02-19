"""We try to submit executables as AML jobs."""

from ._app import Application, AppServices, main

__all__ = [
    "AppServices",
    "Application",
    "main",
]
