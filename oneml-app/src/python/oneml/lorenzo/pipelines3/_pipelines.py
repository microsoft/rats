import logging
from abc import abstractmethod
from threading import Event
from typing import Callable, Protocol, Tuple

logger = logging.getLogger(__name__)


class ITickablePipeline(Protocol):
    @abstractmethod
    def tick(self) -> None:
        pass


class IRunPipelines(Protocol):
    @abstractmethod
    def run_pipeline(self) -> None:
        pass


class IStopPipelines(Protocol):
    @abstractmethod
    def stop_pipeline(self) -> None:
        pass


class ISetPipelines(Protocol):
    @abstractmethod
    def set_pipeline(self, pipeline: ITickablePipeline) -> None:
        pass


class IProvidePipelines(Protocol):
    @abstractmethod
    def get_pipeline(self) -> ITickablePipeline:
        pass


class NullPipeline(ITickablePipeline):
    def tick(self) -> None:
        raise RuntimeError("No pipeline loaded: Null Pipeline not executable")


class PipelineSession(IRunPipelines, IStopPipelines, ISetPipelines):

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


class PipelineChain(ITickablePipeline):

    _chain: Tuple[ITickablePipeline, ...]

    def __init__(self, chain: Tuple[ITickablePipeline, ...]):
        self._chain = chain

    def tick(self) -> None:
        for pipeline in self._chain:
            pipeline.tick()


class DeferredPipeline(ITickablePipeline):

    _provider: Callable[[], ITickablePipeline]

    def __init__(self, provider: Callable[[], ITickablePipeline]):
        self._provider = provider

    def tick(self) -> None:
        self._provider().tick()
