"""Interface for scheduling pipeline steps.

Steps need to interact with three environments:
1. Client environment, which defines them and then schedules them.
1. Scheduling environment, which waits for their inputs to be available, and then allocates and starts a compute environments.
1. Compute environment, which assumes their inputs are ready, reads those inputs, passes them to step.execute, and then writes those outputs.
"""

from __future__ import annotations
from typing import Iterable, Any, Dict, Tuple
from abc import ABC, abstractmethod

class DataIdentifier(ABC):
    """Identifies step inputs and outputs.
    
    To be created by scheduling environment.
    """


class ComputeRequirements(ABC):
    pass


class Step(ABC):
    @abstractmethod
    def set_input_identifiers(**input_name_to_identifier: DataIdentifier) -> StepForScheduling:
        """To be called by client environment, using data identifiers that are outputs of previous steps."""


class StepForScheduling(ABC):
    @abstractmethod
    def get_compute_requirements() -> ComputeRequirements:
        """Get the compute requirements needed to execute this step.
        
        Specified by client environment, and could be a requirement to run in the same python process as the client environment.

        To be called by scheduling environment.
        """

    @abstractmethod
    def get_input_identifiers() -> Dict[str, DataIdentifier]:
        """Get a mapping from input name to input identifier.
        
        To be called by scheduler in order to wait until inputs are ready.

        To be called by compute environment in order to read inputs to be passed to `execute`.
        """

    @abstractmethod
    def get_output_names() -> Iterable[str]:
        """Get the list of output names.  Should be identical to the keys of the outputs of `execute`."""

    @abstractmethod
    def set_output_identifiers(**output_name_to_identifier: DataIdentifier) -> ScheduledStep:
        """To be called by scheduling environment."""


class ScheduledStep(ABC):
    @abstractmethod
    def get_output_identifiers() -> Dict[str, DataIdentifier]:
        """Get a mapping from output name to output identifier.

        To be called by client environment to enable connecting these outputs to downstream steps.

        To be called by compute environment in order to write outputs returned by `execute`.
        """

    @abstractmethod
    def execute(**inputs: Any) -> Iterable[Tuple[str, Any]]:
        """Process the inputs, generating outputs.  Output elements should be tuples of output name to output value.
        
        To be called by compute environment.
        """

    @abstractmethod
    def wait() -> CompletedStep:
        """Wait until step outputs are ready.
        
        
        """


class CompletedStep(ABC):
    @abstractmethod
    def get_output(output_name: str) -> Any:
        """Get the value of an output.  To be called by client environment."""


class SchedulingEnvironment(ABC):
    @abstractmethod
    def schedule(step: StepForScheduling) -> ScheduledStep:
        """Scehdules a step to run once all its inputs are ready."""
