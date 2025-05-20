import logging.config
import warnings
from collections.abc import Iterator
from typing import Any

from rats import apps

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


    # provide the new configuration when executing `logs.ConfigureApplcation`
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
        """Logging should be configured after the execution of this application."""
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
                            "%(log_color)s%(asctime)s %(levelname)-8s [%(name)s][%(lineno)d]: "
                            "%(message)s%(reset)s"
                        ),
                        "datefmt": "%Y-%m-%d %H:%M:%S",
                        "log_colors": {
                            "DEBUG": "white",
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
        logger.debug("done configuring logging")

    @apps.fallback_group(AppConfigs.LOGGERS)
    def _default_loggers(self) -> Iterator[LoggerConfigEntry]:
        yield "", {"level": "INFO", "handlers": ["console"]}
        yield "azure", {"level": "WARNING", "handlers": ["console"]}
