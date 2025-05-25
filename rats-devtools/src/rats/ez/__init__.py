"""
A collection of project-wide utilities exposed through a `rats-ez` cli command.

Unlike many devtool commands, like `rats-ci`, the `rats-ez` commands are expected to be run from
the root of the repo, and help perform operations across components. For example, `rats-ez run`
allows the execution of a given command within every component, to help automate things like
running `poetry update` in each component with one command.
"""

from ._app import Application, main

__all__ = [
    "Application",
    "main",
]
