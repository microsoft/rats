from abc import abstractmethod
from contextlib import contextmanager
from typing import Generator, Optional, Protocol, TypeVar

ContextType = TypeVar("ContextType")

"""
stumped on this one:
src/python/oneml/pipelines/context/_pipelines.py:8:1: error: Invariant type variable "ContextType"
    used in protocol where contravariant one is expected  [misc]
src/python/oneml/pipelines/context/_pipelines.py:15:1: error: Invariant type variable "ContextType"
    used in protocol where covariant one is expected  [misc]
"""


class ISetExecutionContexts(Protocol[ContextType]):  # type: ignore
    @abstractmethod
    @contextmanager
    def execution_context(self, context: ContextType) -> Generator[None, None, None]:
        pass


class IProvideExecutionContexts(Protocol[ContextType]):  # type: ignore
    @abstractmethod
    def get_context(self) -> ContextType:
        pass


class IManageExecutionContexts(
    ISetExecutionContexts[ContextType],
    IProvideExecutionContexts[ContextType],
    Protocol[ContextType],
):
    pass


class ContextClient(IManageExecutionContexts[ContextType]):

    _current: Optional[ContextType]

    def __init__(self) -> None:
        self._current = None

    @contextmanager
    def execution_context(self, context: ContextType) -> Generator[None, None, None]:
        current = self._current
        self._current = context
        try:
            yield
        finally:
            self._current = current

    def get_context(self) -> ContextType:
        if self._current is None:
            raise RuntimeError("no active context found")

        return self._current
