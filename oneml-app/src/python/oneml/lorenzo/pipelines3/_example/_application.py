from typing import Tuple

from oneml.lorenzo.logging import LoggingClient
from oneml.pipelines.session import IExecutable


class Pipeline3ExampleApplication(IExecutable):

    _logging_client: LoggingClient
    _args: Tuple[str, ...]

    def __init__(self, logging_client: LoggingClient, args: Tuple[str, ...]):
        self._logging_client = logging_client
        self._args = args

    def execute(self) -> None:
        self._logging_client.configure_logging()

        print("nothing to do")
