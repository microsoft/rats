import logging
from abc import abstractmethod
from collections import defaultdict
from collections.abc import Generator
from contextlib import AbstractContextManager, contextmanager
from typing import Any, Generic, Protocol, TypeVar

from typing_extensions import NamedTuple

logger = logging.getLogger(__name__)
T_ContextType = TypeVar("T_ContextType", bound=NamedTuple)
Tco_ContextType = TypeVar("Tco_ContextType", bound=NamedTuple, covariant=True)
Tcontra_ContextType = TypeVar("Tcontra_ContextType", bound=NamedTuple, contravariant=True)


class ContextId(NamedTuple, Generic[T_ContextType]):
    name: str


class ContextProvider(Protocol[Tco_ContextType]):
    """
    Callback that returns a single context object.

    This allows us to pass a pre-configured context into a service so the service does not need to
    specify context ids and simply asks for the value.
    """

    @abstractmethod
    def __call__(self) -> Tco_ContextType: ...


class ContextOpener(Protocol[Tcontra_ContextType]):
    ...

    @abstractmethod
    def __call__(self, context: Tcontra_ContextType) -> AbstractContextManager[None]: ...


class IOpenContexts(Protocol):
    def get_context_opener(
        self,
        context_id: ContextId[T_ContextType],
    ) -> ContextOpener[T_ContextType]:
        return lambda context: self.open_context(context_id, context)

    @abstractmethod
    def open_context(
        self,
        context_id: ContextId[T_ContextType],
        value: T_ContextType,
    ) -> AbstractContextManager[None]: ...


class IGetContexts(Protocol):
    def get_context_provider(
        self,
        context_id: ContextId[Tco_ContextType],
    ) -> ContextProvider[Tco_ContextType]:
        return lambda: self.get_context(context_id)

    @abstractmethod
    def get_context(self, context_id: ContextId[T_ContextType]) -> T_ContextType: ...


class IManageContexts(IOpenContexts, IGetContexts, Protocol):
    pass


class ContextClient(IManageContexts):
    _contexts: dict[ContextId[Any], list[Any]]

    def __init__(self) -> None:
        self._contexts = defaultdict(list)

    @contextmanager
    def open_context(  # type: ignore[reportIncompatibleMethodOverride]
        self,
        context_id: ContextId[T_ContextType],
        value: T_ContextType,
    ) -> Generator[None, None, None]:
        self._contexts[context_id].append(value)
        try:
            yield
        finally:
            self._contexts[context_id].pop()

    def get_context(self, context_id: ContextId[Tco_ContextType]) -> Tco_ContextType:
        if len(self._contexts[context_id]) == 0:
            raise RuntimeError(f"context id not found: {context_id}")

        return self._contexts[context_id][-1]
