from abc import abstractmethod
from typing import Generic, Protocol, TypeVar


class IExecutable(Protocol):
    @abstractmethod
    def execute(self) -> None:
        """"""


class NoOpExecutable(IExecutable):

    def execute(self) -> None:
        pass


class ICallableExecutableProvider(Protocol):
    """
    Represents a callable object that returns an IExecutable.

    Useful to type hint callable parameters to methods, especially when used as properties in
    classes. This class also gets around issues with Mypy not allowing Callable[] as a property
    of classes. Use this class as a type hint anywhere you would use Callable[[], IExecutable].
    """
    @abstractmethod
    def __call__(self) -> IExecutable:
        pass


class ICallableExecutable(Protocol):
    """
    Represents a callable object that we expect to treat as the execute method.
    """
    @abstractmethod
    def __call__(self) -> None:
        pass


class DeferredExecutable(IExecutable):
    _callback: ICallableExecutableProvider

    def __init__(self, callback: ICallableExecutableProvider):
        self._callback = callback

    def execute(self) -> None:
        self._callback().execute()


class CallableExecutable(IExecutable):
    _callback: ICallableExecutable

    def __init__(self, callback: ICallableExecutable):
        self._callback = callback

    def execute(self) -> None:
        self._callback()


ContextType = TypeVar("ContextType", contravariant=True)


class IContextualCallableExecutable(Protocol[ContextType]):
    """
    Represents a callable object that we expect to treat as the execute method.
    """
    @abstractmethod
    def __call__(self, context: ContextType) -> None:
        pass


class ContextualCallableExecutable(IExecutable, Generic[ContextType]):

    _context: ContextType
    _callback: IContextualCallableExecutable[ContextType]

    def __init__(
            self,
            context: ContextType,
            callback: IContextualCallableExecutable[ContextType]) -> None:
        self._context = context
        self._callback = callback

    def execute(self) -> None:
        self._callback(context=self._context)
