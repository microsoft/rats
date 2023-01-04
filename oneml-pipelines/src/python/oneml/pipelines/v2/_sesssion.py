from abc import abstractmethod
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, ContextManager, Dict, Generic, Iterable, List, Protocol, Tuple, TypeVar

from oneml.pipelines.session import IExecutable


class IRunnablePipelineSession(Protocol):
    @abstractmethod
    def run(self) -> None:
        pass


class IProvidePipelineSessions(Protocol):
    @abstractmethod
    def get_session(self) -> IRunnablePipelineSession:
        pass


class IProvidePipelineSessionFrames(Protocol):
    @abstractmethod
    def frames(self) -> Iterable[IExecutable]:
        pass


class PipelineSessionFramesClient(IProvidePipelineSessionFrames):

    _frames: Tuple[IExecutable, ...]

    def __init__(self, frames: Tuple[IExecutable, ...]) -> None:
        self._frames = frames

    def frames(self) -> Iterable[IExecutable]:
        return self._frames


# class PipelineSession(IRunnablePipelineSession):
#
#     _session_context: PipelineSessionContext
#     _session_frames_client: IProvidePipelineSessionFrames
#
#     def __init__(
#         self,
#         session_context: PipelineSessionContext,
#         session_frames_client: IProvidePipelineSessionFrames,
#     ) -> None:
#         self._session_context = session_context
#         self._session_frames_client = session_frames_client
#
#     def run(self) -> None:
#         with self._session_context.execution_context(self):
#             for frame in self._session_frames_client.frames():
#                 frame.execute()


PipelineComponentType = TypeVar("PipelineComponentType")


@dataclass(frozen=True)
class PipelineComponentId(Generic[PipelineComponentType]):
    id: str


class PipelineSession:

    _components: Dict[PipelineComponentId[Any], Any]

    def __init__(self) -> None:
        self._components = {}

    def set_component(
        self, id: PipelineComponentId[PipelineComponentType], component: PipelineComponentType
    ) -> None:
        if id in self._components:
            raise RuntimeError(f"Duplicate component found: {id}")

        self._components[id] = component

    def get_component(
        self, id: PipelineComponentId[PipelineComponentType]
    ) -> PipelineComponentType:
        return self._components[id]


class PipelineSessionClient:

    _stack: List[PipelineSession]

    def __init__(self) -> None:
        self._stack = []

    # https://adamj.eu/tech/2021/07/04/python-type-hints-how-to-type-a-context-manager/
    def open(self) -> ContextManager[PipelineSession]:
        @contextmanager
        def generator_function():  # type: ignore
            session = PipelineSession()
            self._stack.append(session)
            yield session
            self._stack.pop()

        # This context manager is written weird because of this bug:
        # https://youtrack.jetbrains.com/issue/PY-36444
        return generator_function()

    def get_current(self) -> PipelineSession:
        return self._stack[-1]


client = PipelineSessionClient()
with client.open() as session1:
    print(session1)
    print(client.get_current())
    with client.open() as session2:
        print(session2)
        print(client.get_current())
    print(client.get_current())
