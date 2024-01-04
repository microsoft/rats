from __future__ import annotations

import functools
from collections.abc import Callable
from pydoc import locate
from typing import Any

from ._pipeline import (
    PM,
    InParameter,
    Inputs,
    OutParameter,
    Outputs,
    ParamCollection,
    ParamEntry,
    UPipeline,
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
                for entry_name, entry in collection._asdict().items()
            )
            if len(entry) > 0
        }
    )


def filter_inputs(inputs: Inputs, predicate: Callable[[InParameter[Any]], bool]) -> Inputs:
    return Inputs(filter_param_collection(inputs, predicate))


def filter_outputs(outputs: Outputs, predicate: Callable[[OutParameter[Any]], bool]) -> Outputs:
    return Outputs(filter_param_collection(outputs, predicate))


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
    def parser_wrapper(pipelines: dict[str, UPipeline], *args: Any, **kwargs: Any) -> object:
        return f(pipelines=list(pipelines.values()), *args, **kwargs)

    return parser_wrapper


def _parse_dependencies_to_list(f: Callable[..., object]) -> Callable[..., object]:
    @functools.wraps(f)
    def parser_wrapper(
        dependencies: dict[str, UPipeline] | None, *args: Any, **kwargs: Any
    ) -> object:
        dps = list(dependencies.values()) if dependencies else None
        return f(dependencies=dps, *args, **kwargs)

    return parser_wrapper
