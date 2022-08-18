from functools import lru_cache
from typing import Tuple

from oneml.lorenzo.logging import LoggingClient
from oneml.pipelines.session import IExecutable

from ._application import Pipeline3ExampleApplication


class Pipeline3DiContainer:

    _args: Tuple[str, ...]

    def __init__(self, args: Tuple[str, ...]):
        self._args = args

    @lru_cache()
    def application(self) -> IExecutable:
        return Pipeline3ExampleApplication(
            logging_client=self._logging_client(),
            args=self._args,
        )

    @lru_cache()
    def _logging_client(self) -> LoggingClient:
        return LoggingClient()
