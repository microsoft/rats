"""
Convenience cli application to help run the example aml jobs.

Each subcommand in this cli will execute an example job that is defined in [rats_e2e.aml][].

```bash
$ python -m rats_e2e.aml.cli --help
Usage: python -m rats_e2e.aml.cli [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  basic-job  Submit the [rats_e2e.aml.basic][] application as an aml job.
```
"""

from ._app import Application, main

__all__ = [
    "Application",
    "main",
]
