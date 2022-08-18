# type: ignore
# flake8: noqa
import logging
from abc import abstractmethod
from typing import Protocol

from oneml.pipelines import (
    ClosePipelineFrameCommand,
    ExecutePipelineFrameCommand,
    IManagePipelineSessionState,
    ITickablePipeline,
    PipelineSessionState,
    PromoteQueuedNodesCommand,
    PromoteRegisteredNodesCommand,
)

logger = logging.getLogger(__name__)


class IRunnablePipelineSession(Protocol):
    @abstractmethod
    def run(self) -> None:
        pass


class IStoppablePipelineSession(Protocol):
    @abstractmethod
    def stop(self) -> None:
        pass


class IPipelineSession(IRunnablePipelineSession, IStoppablePipelineSession, Protocol):
    pass


class DemoPipelineSessionFrame(ITickablePipeline):
    # TODO: turn these ideas into lifecycle events and tools to group events (pre/post)

    _registered: PromoteRegisteredNodesCommand
    _queued: PromoteQueuedNodesCommand
    _execute: ExecutePipelineFrameCommand
    _close: ClosePipelineFrameCommand

    def __init__(
        self,
        registered: PromoteRegisteredNodesCommand,
        queued: PromoteQueuedNodesCommand,
        execute: ExecutePipelineFrameCommand,
        close: ClosePipelineFrameCommand,
    ):
        self._registered = registered
        self._queued = queued
        self._execute = execute
        self._close = close

    def tick(self) -> None:
        logger.debug("running pipeline frame tick()")
        self._registered.execute()
        self._queued.execute()
        self._execute.execute()
        self._close.execute()


class PipelineSession(IPipelineSession):

    _state_client: IManagePipelineSessionState
    _pipeline: ITickablePipeline

    def __init__(self, state_client: IManagePipelineSessionState, pipeline: ITickablePipeline):
        self._state_client = state_client
        self._pipeline = pipeline

    def run(self) -> None:
        self._state_client.set_state(PipelineSessionState.RUNNING)
        while self._state_client.get_state() == PipelineSessionState.RUNNING:
            self._pipeline.tick()

    def stop(self) -> None:
        self._state_client.set_state(PipelineSessionState.STOPPED)
