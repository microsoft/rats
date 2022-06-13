import logging.config


class LoggingClient:

    def configure_logging(self) -> None:
        logging.config.dictConfig({
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "colored": {
                    "()": "colorlog.ColoredFormatter",
                    "format": (
                        "%(log_color)s%(asctime)s %(levelname)-8s [%(name)s][%(lineno)d]: "
                        "%(message)s%(reset)s"),
                    "datefmt": "%Y-%m-%d %H:%M:%S",
                    "log_colors": {
                        "DEBUG": "white",
                        "INFO": "green",
                        "WARNING": "yellow",
                        "ERROR": "red,",
                        "CRITICAL": "bold_red"
                    }
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "level": "DEBUG",
                    "formatter": "colored",
                    "stream": "ext://sys.stdout"
                }
            },
            "loggers": {},
            "root": {
                "level": "DEBUG",
                "handlers": ["console"]
            }
        })
