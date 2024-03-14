from __future__ import annotations

import logging
from abc import abstractmethod
from enum import Enum, auto
from typing import Any, Protocol

from rats.services import ContextProvider

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


class IGetPipelineSessionState(Protocol):
    @abstractmethod
    def get_state(self) -> PipelineSessionState: ...


class ISetPipelineSessionState(Protocol):
    @abstractmethod
    def set_state(self, state: PipelineSessionState) -> None: ...


class IManagePipelineSessionState(
    IGetPipelineSessionState, ISetPipelineSessionState, Protocol
): ...


class PipelineSessionStateClient(IManagePipelineSessionState):
    _state: dict[Any, PipelineSessionState]
    _context: ContextProvider[Any]

    def __init__(self, context: ContextProvider[Any]) -> None:
        self._state = {}
        self._context = context

    def set_state(self, state: PipelineSessionState) -> None:
        self._state[self._context()] = state

    def get_state(self) -> PipelineSessionState:
        ctx = self._context()
        logger.debug(f"getting state for session {ctx}: {self._state[ctx]}")
        return self._state[ctx]
