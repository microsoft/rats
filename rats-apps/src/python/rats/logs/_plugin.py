import logging.config

from rats import apps

logger = logging.getLogger(__name__)


@apps.autoscope
class _PluginEvents:
    CONFIGURE_LOGGING = apps.ServiceId[apps.Executable]("configure-logging")


@apps.autoscope
class PluginServices:
    EVENTS = _PluginEvents


class PluginContainer(apps.Container):
    _app: apps.Container

    def __init__(self, app: apps.Container) -> None:
        self._app = app

    @apps.group(PluginServices.EVENTS.CONFIGURE_LOGGING)
    def _configure_logging(self) -> apps.Executable:
        # in the future, we can use this plugin to make logging easily configurable
        return apps.App(
            lambda: logging.config.dictConfig(
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
                    "root": {"level": "INFO", "handlers": ["console"]},
                }
            )
        )
