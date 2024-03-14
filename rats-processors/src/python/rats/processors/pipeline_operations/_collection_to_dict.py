from collections.abc import Mapping, Sequence
from typing import Any, TypedDict, TypeVar, overload

from ..ux import InPort, InPorts, OutPort, OutPorts, Outputs, Pipeline, UPipeline, UTask
from ._collection_to_dict_processors import DictToOutputs, InputsToDict

T = TypeVar("T")


class CollectionToDictInputs(InPorts[T]):
    col: InPorts[T]


class CollectionToDictOutputs(OutPorts[Mapping[str, T]]):
    dct: OutPort[Mapping[str, T]]


CollectionToDictPL = Pipeline[CollectionToDictInputs[T], CollectionToDictOutputs[T]]


class CollectionToDict:
    @overload
    def __call__(
        self,
        *,
        entries: Sequence[str],
        element_type: type[T],
    ) -> CollectionToDictPL[T]: ...

    @overload
    def __call__(
        self,
        *,
        entries_to_types: Mapping[str, type],
    ) -> CollectionToDictPL[Any]: ...

    def __call__(
        self,
        *,
        entries: Sequence[str] | None = None,
        element_type: type | None = None,
        entries_to_types: Mapping[str, type] | None = None,
    ) -> UPipeline:
        """Convert a collection input into a dictionary output.

        Builds a pipeline that takes a single collection input and outputs a single simple output.
        The output will be a dictionary, where every entry in the input collection becomes an entry
        in the output dictionary.

        Args:
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
        output_type = TypedDict("dct", entries_to_types)  # type: ignore[misc]
        task = UTask(
            processor_type=InputsToDict,
            name="c2d",
            input_annotation=entries_to_types,
            return_annotation={"dct": output_type},
        )
        pipeline = task.rename_inputs(
            {entry_name: f"col.{entry_name}" for entry_name in entries_to_types}
        )
        return pipeline


class DictToCollectionInputs(InPorts[Mapping[str, T]]):
    dct: InPort[Mapping[str, T]]


class DictToCollectionOutCollections(OutPorts[T]):
    col: OutPorts[T]


DictToCollectionPL = Pipeline[DictToCollectionInputs[T], Outputs]


class DictToCollection:
    @overload
    def __call__(
        self,
        *,
        entries: Sequence[str],
        element_type: type[T],
    ) -> DictToCollectionPL[T]: ...

    @overload
    def __call__(
        self,
        *,
        entries_to_types: Mapping[str, type],
    ) -> DictToCollectionPL[Any]: ...

    def __call__(
        self,
        *,
        entries: Sequence[str] | None = None,
        element_type: type | None = None,
        entries_to_types: Mapping[str, type] | None = None,
    ) -> UPipeline:
        """Convert a dictionary input into a collection output.

        Builds a pipeline that takes a single simple input and outputs a single collection output.
        The input is assumed to be a dictionary with a predefined set of entries, as specified by
        the `entries_to_types` argument. The output will be a collection, where every entry in the
        input dictionary becomes an entry in the output collection.

        Args:
            entries: name of the entries in the input dictionary and output collection.
            element_type: type of each element in the input dictionary and output collection.
            entries_to_types: name of the entries in the input dictionary and output collection,
                each mapped to its type.
        """
        if entries_to_types is None:
            assert entries is not None
            assert element_type is not None
            entries_to_types = {entry: element_type for entry in entries}
        else:
            assert entries is None
            assert element_type is None
        task = UTask(
            processor_type=DictToOutputs,
            name="d2c",
            return_annotation=entries_to_types,
        )
        pipeline = task.rename_outputs(
            {entry_name: f"col.{entry_name}" for entry_name in entries_to_types}
        )
        return pipeline
