# This defines the interface of _legacy_subpackages for use by the rest of rats.processors.


from . import _typing as typing
from ._container import (
    LegacyServicesWrapperContainer,
    Services,
)
from ._interfaces import IPipelineRunner, IPipelineRunnerFactory, IPipelineToDot
from .ux import CombinedPipeline, Task

__all__ = [
    "Task",
    "CombinedPipeline",
    "typing",
    "IPipelineRunner",
    "IPipelineRunnerFactory",
    "IPipelineToDot",
    "LegacyServicesWrapperContainer",
    "Services",
]
