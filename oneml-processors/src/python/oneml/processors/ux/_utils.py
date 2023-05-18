from __future__ import annotations

import functools
from pydoc import locate
from typing import TYPE_CHECKING, Any, Callable

from ._pipeline import (
    PC,
    PL,
    PM,
    InCollections,
    InParameter,
    Inputs,
    IOCollections,
    OutCollections,
    OutParameter,
    Outputs,
    ParamCollection,
    ParamEntry,
    Pipeline,
)


def filter_param_collection(
    collection: ParamCollection[ParamEntry[PM]], predicate: Callable[[PM], bool]
) -> ParamCollection[ParamEntry[PM]]:
    return collection.__class__(
        {
            entry_name: entry
            for entry_name, entry in (
                (
                    entry_name,
                    entry.__class__(in_param for in_param in entry if predicate(in_param)),
                )
                for entry_name, entry in collection.items()
            )
            if len(entry) > 0
        }
    )


def filter_inputs(inputs: Inputs, predicate: Callable[[InParameter], bool]) -> Inputs:
    return Inputs(filter_param_collection(inputs, predicate))


def filter_outputs(outputs: Outputs, predicate: Callable[[OutParameter], bool]) -> Outputs:
    return Outputs(filter_param_collection(outputs, predicate))


def filter_io_collection(
    collections: IOCollections[ParamCollection[ParamEntry[PM]]], predicate: Callable[[PM], bool]
) -> IOCollections[ParamCollection[ParamEntry[PM]]]:
    return collections.__class__(
        {
            collection_name: collection
            for collection_name, collection in (
                (
                    collection_name,
                    filter_param_collection(collection, predicate),
                )
                for collection_name, collection in collections.items()
            )
            if len(collection) > 0
        }
    )


def filter_in_collections(
    in_collections: InCollections, predicate: Callable[[InParameter], bool]
) -> InCollections:
    return InCollections(filter_io_collection(in_collections, predicate))


def filter_out_collections(
    out_collections: OutCollections, predicate: Callable[[OutParameter], bool]
) -> OutCollections:
    return OutCollections(filter_io_collection(out_collections, predicate))


def _processor_type(f: Callable[..., object]) -> Callable[..., object]:
    def locate_processor_type(processor_type: str, *args: Any, **kwargs: Any) -> object:
        return f(processor_type=locate(processor_type), *args, **kwargs)

    return locate_processor_type


def _input_annotation(f: Callable[..., object]) -> Callable[..., object]:
    def loc_intype(input_annotation: dict[str, str] | None, *args: Any, **kwargs: Any) -> object:
        loc = {k: locate(v) for k, v in input_annotation.items()} if input_annotation else None
        return f(input_annotation=loc, *args, **kwargs)

    return loc_intype


def _return_annotation(f: Callable[..., object]) -> Callable[..., object]:
    def loc_rettype(return_annotation: dict[str, str] | None, *args: Any, **kwargs: Any) -> object:
        loc = {k: locate(v) for k, v in return_annotation.items()} if return_annotation else None
        return f(return_annotation=loc, *args, **kwargs)

    return loc_rettype


def _parse_pipelines_to_list(f: Callable[..., object]) -> Callable[..., object]:
    @functools.wraps(f)
    def parser_wrapper(pipelines: dict[str, Pipeline], *args: Any, **kwargs: Any) -> object:
        return f(pipelines=list(pipelines.values()), *args, **kwargs)

    return parser_wrapper


def _parse_dependencies_to_list(f: Callable[..., object]) -> Callable[..., object]:
    @functools.wraps(f)
    def parser_wrapper(
        dependencies: dict[str, Pipeline] | None, *args: Any, **kwargs: Any
    ) -> object:
        dps = list(dependencies.values()) if dependencies else None
        return f(dependencies=dps, *args, **kwargs)

    return parser_wrapper
