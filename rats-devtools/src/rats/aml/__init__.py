"""
Submit applications as aml jobs, sending necessary context from the driver node.

This module combines the capabilities of [rats.app_context][] and [rats.runtime][] module to allow
the execution of any registered `rats.runtime.apps` entry-point as an aml job. The `rats-aml` cli
command provides a basic interface to submit jobs from the terminal, and the [rats.aml.submit][]
function provides a python api for submitting jobs with much more access to configuration, and the
ability to submit more than one job from a single process.

```
$ rats-aml
Usage: rats-aml [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  list    List all the exes and groups that announce their availability to be
          submitted to aml.

          This command is currently an alias to the `rats-runtime list`
          command because [rats.aml][] should be able to run anything `rats-
          runtime` can. Any application registered to the `rats.runtime.apps`
          python entry-point.
  submit  Submit one or more apps to aml.

          Run `rats-aml list` to find the list of applications registered in
          this component.
```
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
