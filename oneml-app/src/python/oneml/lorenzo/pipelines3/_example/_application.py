from typing import Tuple

from oneml.lorenzo.logging import LoggingClient
from oneml.lorenzo.pipelines3 import IExecutable, IProvidePipelines, PipelineSession


class Pipeline3ExampleApplication(IExecutable):

    _logging_client: LoggingClient
    _args: Tuple[str, ...]
    _pipeline_session: PipelineSession
    _pipeline_provider: IProvidePipelines

    def __init__(
            self,
            logging_client: LoggingClient,
            args: Tuple[str, ...],
            pipeline_session: PipelineSession,
            pipeline_provider: IProvidePipelines):
        self._logging_client = logging_client
        self._args = args
        self._pipeline_session = pipeline_session
        self._pipeline_provider = pipeline_provider

    def execute(self) -> None:
        self._logging_client.configure_logging()

        self._pipeline_session.set_pipeline(self._pipeline_provider.get_pipeline())
        self._pipeline_session.run_pipeline()
