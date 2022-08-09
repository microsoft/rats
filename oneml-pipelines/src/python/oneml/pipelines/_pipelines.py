import logging
from abc import abstractmethod
from threading import Event
from typing import Protocol, Tuple

logger = logging.getLogger(__name__)


class ITickablePipeline(Protocol):
    @abstractmethod
    def tick(self) -> None:
        """"""


class IRunPipelines(Protocol):
    @abstractmethod
    def run_pipeline(self) -> None:
        """"""


class IStopPipelines(Protocol):
    @abstractmethod
    def stop_pipeline(self) -> None:
        """"""


class ISetPipelines(Protocol):
    @abstractmethod
    def set_pipeline(self, pipeline: ITickablePipeline) -> None:
        """"""


class IProvidePipelines(Protocol):
    @abstractmethod
    def get_pipeline(self) -> ITickablePipeline:
        """
        """


class IManagePipelines(IRunPipelines, IStopPipelines, ISetPipelines, IProvidePipelines, Protocol):
    """
    """


class NullPipeline(ITickablePipeline):
    def tick(self) -> None:
        raise RuntimeError("No pipeline loaded: Null Pipeline not executable")


class PipelineSession(IManagePipelines):

    _is_running: Event
    _pipeline: ITickablePipeline

    def __init__(self, pipeline: ITickablePipeline):
        self._pipeline = pipeline

        self._is_running = Event()

    def set_pipeline(self, pipeline: ITickablePipeline) -> None:
        self._pipeline = pipeline

    def run_pipeline(self) -> None:
        while not self._is_running.is_set():
            self._pipeline.tick()

    def stop_pipeline(self) -> None:
        self._is_running.set()

    def get_pipeline(self) -> ITickablePipeline:
        return self._pipeline


class PipelineChain(ITickablePipeline):

    _chain: Tuple[ITickablePipeline, ...]

    def __init__(self, chain: Tuple[ITickablePipeline, ...]):
        self._chain = chain

    def tick(self) -> None:
        for pipeline in self._chain:
            pipeline.tick()


class ICallablePipelineProvider(Protocol):
    @abstractmethod
    def __call__(self) -> ITickablePipeline:
        pass


class DeferredPipeline(ITickablePipeline):

    _provider: ICallablePipelineProvider

    def __init__(self, provider: ICallablePipelineProvider):
        self._provider = provider

    def tick(self) -> None:
        self._provider().tick()
