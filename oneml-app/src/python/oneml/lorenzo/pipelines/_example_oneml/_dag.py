from typing import Tuple

from oneml.lorenzo.pipelines import PipelineStep


class PipelineDag:

    _steps: Tuple[PipelineStep, ...]

    def execute(self) -> None:
        for step in self._steps:
            step.execute()


"""
Pipeline Data Management Layer?
"""
