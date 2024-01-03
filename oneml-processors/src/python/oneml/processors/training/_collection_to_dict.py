from collections.abc import Mapping
from typing import Any, TypedDict, overload

from ..ux import UPipeline, UTask


class InputsToDict:
    def __init__(self, output_name: str) -> None:
        self._output_name = output_name

    def process(self, **kwds: Any) -> Mapping[str, Any]:
        return {self._output_name: kwds}


class CollectionToDictBuilder:
    @overload
    @classmethod
    def build(
        cls,
        collection_name: str,
        *,
        entries: set[str],
        element_type: type,
    ) -> UPipeline:
        ...

    @overload
    @classmethod
    def build(
        cls,
        collection_name: str,
        *,
        entries_to_types: Mapping[str, type],
    ) -> UPipeline:
        ...

    @classmethod
    def build(
        cls,
        collection_name: str,
        *,
        entries: set[str] | None = None,
        element_type: type | None = None,
        entries_to_types: Mapping[str, type] | None = None,
    ) -> UPipeline:
        """Convert a collection input into a dictionary output.

        Builds a pipeline that takes a single collection input and outputs a single simple output.
        The output will be a dictionary, where every entry in the input collection becomes an entry
        in the output dictionary.

        Args:
            collection_name: name of the input collection and output simple.
            entries: name of the entries in the input collection and output dictionary.
            element_type: type of each element in the input collection.
            entries_to_types: name of the entries in the input collection and output dictionary,
                each mapped to its type.
        """
        if entries_to_types is None:
            assert entries is not None
            assert element_type is not None
            entries_to_types = {entry: element_type for entry in entries}
        else:
            assert entries is None
            assert element_type is None
        output_type = TypedDict(collection_name, entries_to_types)  # type: ignore[misc]
        task = UTask(
            processor_type=InputsToDict,
            name="collect",
            config=dict(output_name=collection_name),
            input_annotation=entries_to_types,
            return_annotation={collection_name: output_type},
        )
        pipeline: UPipeline = task.rename_inputs(
            {entry: f"{collection_name}.{entry}" for entry in entries_to_types}
        )
        return pipeline
