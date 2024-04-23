from collections.abc import Sequence
from typing import Any
from uuid import uuid4

from rats import apps
from rats.processors import _types as rpt
from rats.processors._legacy_subpackages import ux


class PipelineContainer(apps.AnnotatedContainer):
    """Specialized container for defining pipelines.

    Exposes functionality for defining tasks and pipelines.
    """

    def combine(
        self,
        pipelines: Sequence[rpt.UPipeline],
        name: str | None = None,
        dependencies: Sequence[rpt.DependencyOp[Any]] | None = None,
        inputs: rpt.UserInput | None = None,
        outputs: rpt.UserOutput | None = None,
    ) -> rpt.UPipeline:
        name = name or uuid4().hex
        return ux.CombinedPipeline(
            pipelines=pipelines,
            name=name,
            dependencies=dependencies,
            inputs=inputs,
            outputs=outputs,
        )
