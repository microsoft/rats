"""
Small module to help configure logging for rats applications.

We provide a rats application that can be executed at the beginning of your process, that will
handle configuring the python logging libraries, with a few configuration options being exposed.

!!! warning
    We expose the logging functionality through a [rats.apps.AppContainer][] in order to leverage
    the built in plugin system to give users the ability to adjust the default settings, but this
    application should be lightweight and should not contain very complex logic, avoiding logic
    that is very time consuming or has a chance of failing with confusing errors.

## Verbosity Env Variables

To help develop modules, logging output can be configured with the `DEBUG_LOGS_*`, `QUIET_LOGS_*`,
and `LEVEL_LOGS_*` environment variables. The suffix of the environment variables match the module
name wanting to be configured.

### Module Loggers

Environment variables named `DEBUG_LOGS_*` cause logs from the given module to be shown; the
`QUIET_LOGS_*` environment variables silence logs emitted by the module; and `LEVEL_LOGS_*` allows
a specific [logging-level](https://docs.python.org/3/library/logging.html#logging-levels) to be
used.

```
$ rats-ci fix
All checks passed!
63 files left unchanged
ran 2 fix commands
```

```bash
# Enable DEBUG level logs for the `rats.*` modules
export DEBUG_LOGS_RATS="1"
# Enable WARNING level logs for the `rats.projects.*` modules
export LEVEL_LOGS_RATS_PROJECTS="WARNING"
# Disable logs for `rats.cli.*` modules
export QUIET_LOGS_RATS_CLI="1"
```
```
$ rats-ci fix
2025-05-27 00:49:45 DEBUG    [rats.logs._app:96]: done configuring logging
All checks passed!
63 files left unchanged
ran 2 fix commands
```

### Root Logger

The root logger can be configured with the `DEBUG_LOGS`, `QUIET_LOGS`, and `LEVEL_LOGS` environment
variables.

```bash
# Enable WARNING level logs for all logs
export LEVEL_LOGS="WARNING"
```

"""

from ._app import AppConfigs, ConfigureApplication
from ._showwarning import showwarning

__all__ = [
    "AppConfigs",
    "ConfigureApplication",
    "showwarning",
]
