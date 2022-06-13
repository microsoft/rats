from typing import Callable, List, Tuple

from ._pipeline_step import PipelineStep


class DeferredStep(PipelineStep):

    _callback: Callable[[], PipelineStep]

    def __init__(self, callback: Callable[[], PipelineStep]):
        self._callback = callback

    def execute(self) -> None:
        step = self._callback()
        step.execute()


class DeferredChain(PipelineStep):

    _step_callbacks: Tuple[Callable[[], PipelineStep], ...]

    def __init__(self, step_callbacks: Tuple[Callable[[], PipelineStep], ...]):
        self._step_callbacks = step_callbacks

    def execute(self) -> None:
        for callback in self._step_callbacks:
            step = callback()
            step.execute()


class DeferredChainBuilder:

    _callbacks: List[Callable[[], PipelineStep]]

    def __init__(self):
        self._callbacks = []

    def add(self, callback: Callable[[], PipelineStep]) -> None:
        self._callbacks.append(callback)

    def build(self) -> DeferredChain:
        return DeferredChain(step_callbacks=tuple(self._callbacks))
