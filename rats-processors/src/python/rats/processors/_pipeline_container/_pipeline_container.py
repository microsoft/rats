from collections.abc import Sequence
from typing import Any
from uuid import uuid4

from rats import apps
from rats.processors._legacy_subpackages import ux


class PipelineContainer(apps.AnnotatedContainer):
    """Specialized container for defining pipelines.

    Exposes functionality for defining tasks and pipelines.
    """

    def combine(
        self,
        pipelines: Sequence[ux.UPipeline],
        name: str | None = None,
        dependencies: Sequence[ux.DependencyOp[Any]] | None = None,
        inputs: ux.UserInput | None = None,
        outputs: ux.UserOutput | None = None,
    ) -> ux.UPipeline:
        name = name or uuid4().hex
        return ux.CombinedPipeline(
            pipelines=pipelines,
            name=name,
            dependencies=dependencies,
            inputs=inputs,
            outputs=outputs,
        )
