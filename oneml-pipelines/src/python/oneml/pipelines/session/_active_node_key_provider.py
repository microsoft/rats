from abc import abstractmethod
from typing import Protocol

from ...services._context import ContextClient
from ._context import OnemlSessionContextIds


class IActiveNotKeyProvider(Protocol):
    @abstractmethod
    def __call__(self) -> str:
        ...


class ActiveNotKeyProvider(IActiveNotKeyProvider):
    _context_client: ContextClient

    def __init__(self, context_client: ContextClient):
        self._context_client = context_client

    def __call__(self) -> str:
        node = self._context_client.get_context(OnemlSessionContextIds.NODE_ID)
        key = node.key
        return key
