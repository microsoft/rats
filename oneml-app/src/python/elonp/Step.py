"""Interface for scheduling pipeline steps.

Steps need to interact with three environments:
1. Client environment, which defines them and then schedules them.
1. Scheduling environment, which waits for their inputs to be available, and then allocates and starts a compute environments.
1. Compute environment, which assumes their inputs are ready, reads those inputs, passes them to step.execute, and then writes those outputs.
"""

from __future__ import annotations
from typing import Iterable, Any, Dict


class DataIdentifier:
    """Identifies step inputs and outputs.
    
    To be created by scheduling environment.
    """


class ComputeRequirements:
    """"""

class Step:
    def execute(**input_name_to_value: Any) -> Dict[str, Any]:
        """Execute the step logic given its inputs.  To be called in the environment in which the step should run."""

    def set_input_identifiers(**input_name_to_identifier: DataIdentifier) -> StepForScheduling:
        """To be called by client environment, using data identifiers that are outputs of previous steps."""

    def get_compute_requirements() -> ComputeRequirements:
        """To be called by scheduling environment."""


class StepForScheduling:
    def get_input_identifiers() -> Dict[str, DataIdentifier]:
        """Get a mapping from input name to input identifier.
        
        To be called by scheduler in order to wait until inputs are ready.

        To be called by compute environment in order to read inputs to be passed to `execute`.
        """

    def get_output_names() -> Iterable[str]:
        """Get the list of output names.  Should be identical to the keys of the outputs of `execute`."""

    def set_output_identifiers(**output_name_to_identifier: DataIdentifier) -> ScheduledStep:
        """To be called by scheduling environment."""

    def execute(**input_name_to_value: Any) -> Dict[str, Any]:
        """Execute the step logic given its inputs.  To be called in the environment in which the step should run."""


class ScheduledStep:
    def get_output_identifiers() -> Dict[str, DataIdentifier]:
        """Get a mapping from output name to output identifier.

        To be called by client environment to enable connecting these outputs to downstream steps.

        To be called by compute environment in order to write outputs returned by `execute`.
        """

    def wait() -> CompletedStep:
        """Wait until step outputs are ready."""


class CompletedStep:
    def get_output(output_name: str) -> Any:
        """Get the value of an output.  To be called by client environment."""


class SchedulingEnvironment:
    def schedule(step: StepForScheduling) -> ScheduledStep:
        """Scehdules a step to run once all its inputs are ready."""


