from typing import Any, Mapping

from oneml.processors.utils import frozendict
from oneml.processors.ux import UPipeline, UTask, find_non_clashing_name

from ._expose_given_outputs_processor import ExposeGivenOutputsProcessor


class ExposeGivenOutputs:
    def __call__(
        self,
        outputs: Mapping[str, Any] = dict(),
        out_collections: Mapping[str, Mapping[str, Any]] = dict(),
    ) -> UPipeline:
        combined_data = dict(**outputs)
        renames = dict()
        for collection_name, collection in out_collections.items():
            for entry_name, value in collection.items():
                key = find_non_clashing_name(f"{collection_name}_{entry_name}", set(combined_data))
                renames[key] = f"{collection_name}.{entry_name}"
                combined_data[key] = value
        frozen_outputs = frozendict(combined_data)

        return_annotation = frozendict({k: type(v) for k, v in combined_data.items()})
        pl = UTask(
            ExposeGivenOutputsProcessor,
            name="fixed_output",
            config=frozendict(outputs=frozen_outputs),
            return_annotation=return_annotation,
        ).rename_outputs(renames)
        return pl
