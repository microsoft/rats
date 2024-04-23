from collections.abc import Mapping
from typing import Any, TypeVar

from rats.processors._legacy_subpackages.utils import frozendict, namedcollection
from rats.processors._legacy_subpackages.ux import Task, UPipeline

from ._expose_given_outputs_processor import ExposeGivenOutputsProcessor

TOutputs = TypeVar("TOutputs")


class ExposeGivenOutputs:
    def __call__(self, outputs: Mapping[str, Any] = dict()) -> UPipeline:
        data = namedcollection(outputs)
        return_annotation = frozendict({k: type(v) for k, v in outputs.items()})
        return Task(
            ExposeGivenOutputsProcessor,
            name="fixed_output",
            config=frozendict(outputs=data),
            return_annotation=return_annotation,
        ).rename_outputs({k: k for k in outputs})
