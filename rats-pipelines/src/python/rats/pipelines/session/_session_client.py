import logging
from abc import abstractmethod
from typing import Protocol

from rats.services import IExecutable

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


class PipelineSessionClient(IPipelineSession):
    _session_frame: IExecutable
    _session_state_client: IManagePipelineSessionState

    def __init__(
        self,
        session_frame: IExecutable,
        session_state_client: IManagePipelineSessionState,
    ) -> None:
        self._session_frame = session_frame
        self._session_state_client = session_state_client

    def run(self) -> None:
        # TODO: if we use a context for session states, I think I can fix the node registration
        #  rough edges
        logger.debug("setting session state to running")
        self._session_state_client.set_state(PipelineSessionState.RUNNING)
        while self._session_state_client.get_state() == PipelineSessionState.RUNNING:
            logger.debug("ticking the pipeline forward")
            self._session_frame.execute()
        logger.debug("pipeline session is done running")

    def stop(self) -> None:
        self._session_state_client.set_state(PipelineSessionState.STOPPED)
