"""
A minimal example application that can be submitted as an aml job.

We can run the examples with the cli commands in the [rats_e2e.aml][] module.

```bash
$ python -m rats_e2e.aml --help
Usage: python -m rats_e2e.aml [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  basic-job  Submit the [rats_e2e.aml.basic][] application as an aml job
```

The [rats_e2e.aml.basic.Application][] class contains a small amount of code we want to execute
within an aml job. It outputs information provided to it by the job submitter. We can submit this
job through the `rats-aml submit` cli command, or by using the [rats.aml.submit][] function within
python code.
"""
from ._app import Application, AppServices, ExampleData

__all__ = [
    "AppServices",
    "Application",
    "ExampleData",
]
