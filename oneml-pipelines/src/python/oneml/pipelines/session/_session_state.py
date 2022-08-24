from __future__ import annotations

import logging
from abc import abstractmethod
from enum import Enum, auto
from typing import Protocol

logger = logging.getLogger(__name__)


class PipelineSessionState(Enum):
    PENDING = auto()
    """
    """

    RUNNING = auto()
    """
    """

    STOPPED = auto()
    """
    """


class ILocatePipelineSessionState(Protocol):
    @abstractmethod
    def get_state(self) -> PipelineSessionState:
        """ """


class ISetPipelineSessionState(Protocol):
    @abstractmethod
    def set_state(self, state: PipelineSessionState) -> None:
        """ """


class IManagePipelineSessionState(ILocatePipelineSessionState, ISetPipelineSessionState, Protocol):
    """ """


class PipelineSessionStateClient(IManagePipelineSessionState):
    _current_state: PipelineSessionState

    def __init__(self) -> None:
        self._current_state = PipelineSessionState.PENDING

    def set_state(self, state: PipelineSessionState) -> None:
        self._current_state = state

    def get_state(self) -> PipelineSessionState:
        return self._current_state
