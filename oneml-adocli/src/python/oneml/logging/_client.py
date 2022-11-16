import logging.config
from abc import abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Protocol


@dataclass(frozen=True)
class PackageLogLevel:
    package: str
    level: str


class IUpdateLogLevels(Protocol):
    @abstractmethod
    def set_log_levels(self, *args: PackageLogLevel) -> None:
        pass


class IApplyLogConfigs(Protocol):
    @abstractmethod
    def apply_config(self) -> None:
        pass


class LoggingClient(IUpdateLogLevels, IApplyLogConfigs):

    _current_config: Dict[str, Any]

    def __init__(self):
        self._current_config = {
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
                    "stream": "ext://sys.stderr"
                }
            },
            "loggers": {},
            "root": {
                "level": "DEBUG",
                "handlers": ["console"]
            }
        }

    def set_log_levels(self, *args: PackageLogLevel) -> None:
        for thing in args:
            self._current_config["loggers"][thing.package] = {"level": thing.level}

    def apply_config(self) -> None:
        logging.config.dictConfig(self._current_config)
