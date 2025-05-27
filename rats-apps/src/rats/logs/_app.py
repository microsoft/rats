import logging.config
import os
import warnings
from collections.abc import Iterator
from typing import Any

from rats import apps

from ._showwarning import showwarning

logger = logging.getLogger(__name__)
LoggerConfigEntry = tuple[str, dict[str, Any]]


@apps.autoscope
class AppConfigs:
    LOGGERS = apps.ServiceId[LoggerConfigEntry]("loggers.config-group")
    """
    Register additional loggers to this service group.

    ```python
    from rats import apps


    class PluginContainer(apps.Container, apps.PluginMixin):
        @apps.group(AppConfigs.LOGGERS)
        def _custom_loggers(self) -> Iterator[LoggerConfigEntry]:
            yield "", {"level": "INFO", "handlers": ["console"]}
            yield "azure", {"level": "WARNING", "handlers": ["console"]}


    # provide the new configuration when executing `logs.ConfigureAppilcation`
    apps.run(apps.AppBundle(
        app_plugin=logs.ConfigureApplication,
        container_plugin=PluginContainer,
    ))
    ```
    """


class ConfigureApplication(apps.AppContainer, apps.PluginMixin):
    """
    Configure logging for the current process.

    We try to provide some simple default loggers, but you can replace the loggers by providing the
    [rats.logs.AppConfigs.LOGGERS][] service group.

    ```python
    from rats import apps, logs

    apps.run(apps.AppBundle(app_plugin=logs.ConfigureApplication))
    ```
    """

    def execute(self) -> None:
        """Applies the logging configuration."""
        logger_configs = self._app.get_group(AppConfigs.LOGGERS)
        loggers_dict = {key: value for key, value in logger_configs}
        logging.config.dictConfig(
            {
                "version": 1,
                "disable_existing_loggers": False,
                "formatters": {
                    "colored": {
                        "()": "colorlog.ColoredFormatter",
                        "format": (
                            "%(log_color)s%(asctime)s %(levelname)-8s [%(name)s:%(lineno)d]: "
                            "%(message)s%(reset)s"
                        ),
                        "datefmt": "%Y-%m-%d %H:%M:%S",
                        "log_colors": {
                            "DEBUG": "cyan",
                            "INFO": "green",
                            "WARNING": "yellow",
                            "ERROR": "red,",
                            "CRITICAL": "bold_red",
                        },
                    }
                },
                "handlers": {
                    "console": {
                        "class": "logging.StreamHandler",
                        "level": "DEBUG",
                        "formatter": "colored",
                        "stream": "ext://sys.stderr",
                    }
                },
                "loggers": loggers_dict,
            }
        )
        # enable deprecation warnings by default
        logging.captureWarnings(True)
        warnings.simplefilter("default", DeprecationWarning)
        # our modified `showwarning` method logs warnings with the module logger that emitted it
        warnings.showwarning = showwarning
        logger.debug("done configuring logging")

    @apps.fallback_group(AppConfigs.LOGGERS)
    def _default_loggers(self) -> Iterator[LoggerConfigEntry]:
        logger_mapping = {
            "": "INFO",
            "azure": "WARNING",
            "py.warnings": "CRITICAL",
        }
        searched_prefixes = [
            "DEBUG_LOGS",
            "QUIET_LOGS",
            "LEVEL_LOGS",
        ]
        for name in os.environ.keys():
            env_prefix = name[0:10]
            if env_prefix not in searched_prefixes:
                # this isn't a logging config env
                continue

            # our above prefixes are conveniently all 10 characters
            # everything after the prefix is the logger name, skip the underscore after the prefix
            logger_name = name.lower()[11:].replace("_", ".")
            if logger_name not in logger_mapping:
                # the default here is ignored
                logger_mapping[logger_name] = "INFO"

        for name, default in logger_mapping.items():
            yield self._build_logger_entry(name, default)

    def _build_logger_entry(self, name: str, default: str = "INFO") -> LoggerConfigEntry:
        # https://docs.python.org/3/library/logging.html#logging-levels
        valid_levels = [
            "NOTSET",
            "DEBUG",
            "INFO",
            "WARNING",
            "ERROR",
            "CRITICAL",
        ]
        suffix = f"_{'_'.join(name.split('.')).upper()}" if name != "" else ""

        debug_env_name = f"DEBUG_LOGS{suffix}"
        quiet_env_name = f"QUIET_LOGS{suffix}"
        level_env_name = f"LEVEL_LOGS{suffix}"
        if os.environ.get(level_env_name):
            # user specified exactly what log level is wanted for this module
            lvl = os.environ[level_env_name].upper()
            if lvl not in valid_levels:
                raise ValueError(f"invalid log level specified: {level_env_name}={lvl}")
            return name, {"level": lvl, "handlers": ["console"], "propagate": False}
        elif os.environ.get(debug_env_name):
            # show as many logs as possible
            return name, {"level": "DEBUG", "handlers": ["console"], "propagate": False}
        elif os.environ.get(quiet_env_name):
            # only show critical logs when QUIET_LOGS is enabled
            return name, {"level": "CRITICAL", "handlers": ["console"], "propagate": False}
        else:
            # set default logging to INFO
            return name, {"level": default, "handlers": ["console"], "propagate": False}
