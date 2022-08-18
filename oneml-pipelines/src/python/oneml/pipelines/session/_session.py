import logging
from abc import abstractmethod
from typing import Protocol

from ._session_frame import IPipelineSessionFrame
from ._session_state import IManagePipelineSessionState, PipelineSessionState

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


class PipelineSession(IPipelineSession):

    _session_state_client: IManagePipelineSessionState
    _session_frame: IPipelineSessionFrame

    def __init__(
            self,
            session_state_client: IManagePipelineSessionState,
            session_frame: IPipelineSessionFrame) -> None:
        self._session_state_client = session_state_client
        self._session_frame = session_frame

    def run(self) -> None:
        self._session_state_client.set_state(PipelineSessionState.RUNNING)
        while self._session_state_client.get_state() == PipelineSessionState.RUNNING:
            self._session_frame.tick()

    def stop(self) -> None:
        self._session_state_client.set_state(PipelineSessionState.STOPPED)
