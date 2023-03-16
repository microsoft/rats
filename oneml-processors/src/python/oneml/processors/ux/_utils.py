from __future__ import annotations

import functools
from pydoc import locate
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from oneml.processors.ux import Pipeline


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
