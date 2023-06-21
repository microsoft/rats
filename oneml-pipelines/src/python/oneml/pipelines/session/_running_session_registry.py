from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from ..dag import PipelineSessionId

if TYPE_CHECKING:
    from ._session_client import PipelineSessionClient


class IGetSessionClient(Protocol):
    def get(self, session_id: PipelineSessionId) -> PipelineSessionClient:
        pass


class RunningSessionRegistry(IGetSessionClient):
    _data: dict[PipelineSessionId, PipelineSessionClient]

    def __init__(self) -> None:
        self._data = {}

    def set(self, session_id: PipelineSessionId, session_client: PipelineSessionClient) -> None:
        self._data[session_id] = session_client

    def unset(self, session_id: PipelineSessionId) -> None:
        del self._data[session_id]

    def get(self, session_id: PipelineSessionId) -> PipelineSessionClient:
        return self._data[session_id]
