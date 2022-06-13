from abc import ABC, abstractmethod
from typing import Tuple


class PipelineStep(ABC):
    @abstractmethod
    def execute(self) -> None:
        """Implement the business logic for the pipeline step."""


class PipelineStepJob(ABC):
    """
    A job is the definition of a task running in a specific environment.
    """
    # step: PipelineStep
    # execution_context: PipelineExecutionContext


class SimplePipeline(PipelineStep):
    """
    Maybe rename this to `SequentialPipeline`?

    - This is more related to orchestration than anything else.
    """

    _steps: Tuple[PipelineStep, ...]

    def __init__(self, steps: Tuple[PipelineStep, ...]):
        self._steps = steps

    def execute(self) -> None:
        for step in self._steps:
            step.execute()

# Can we make a set of classes that eliminate the need to define the storage logic?
# Most pipeline steps probably use the same storage logic.
