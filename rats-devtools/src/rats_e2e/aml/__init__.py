"""
Examples and end-to-end tests for the `rats.aml` package.

The [rats_e2e.aml][] module has a small cli application that runs end-to-end tests that can be used
as examples for different patterns for submitting jobs to aml. It's not exposed as a component
script, but the cli can be run in the terminal with `python -m rats_e2e.aml` and our basic aml job
can be run with `python -m rats_e2e.aml basic-job` or with the `rats-aml` command using
`rats-aml submit rats_e2e.aml.hello-world`. Read the documentation for the example jobs to dive
deeper into ways to create and run aml jobs.
"""

from ._app import Application, main

__all__ = [
    "Application",
    "main",
]
