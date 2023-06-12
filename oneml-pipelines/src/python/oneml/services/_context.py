from contextlib import contextmanager
from typing import Any, Dict, Generator, Generic, TypeVar

from typing_extensions import NamedTuple

ContextType = TypeVar("ContextType", bound=NamedTuple)


class ContextId(NamedTuple, Generic[ContextType]):
    name: str


class ContextClient:

    _contexts: Dict[ContextId[Any], Any]

    def __init__(self) -> None:
        self._contexts = {}

    @contextmanager
    def open_context(
        self,
        context_id: ContextId[ContextType],
        value: ContextType,
    ) -> Generator[None, None, None]:
        if context_id in self._contexts:
            # TODO: figure out if we prefer allowing this and storing contexts as a stack
            raise RuntimeError(f"context id already in use: {context_id}")

        self._contexts[context_id] = value
        try:
            yield
        finally:
            del self._contexts[context_id]

    def get_context(self, context_id: ContextId[ContextType]) -> ContextType:
        if context_id not in self._contexts:
            raise RuntimeError(f"context id not found: {context_id}")

        return self._contexts[context_id]
