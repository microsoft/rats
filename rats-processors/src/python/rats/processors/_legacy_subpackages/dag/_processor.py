from __future__ import annotations

import logging
import sys
from abc import ABC
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from enum import Enum
from inspect import _ParameterKind, formatannotation, get_annotations, signature
from typing import (
    Any,
    NamedTuple,
    Protocol,
    Union,  # pyright: ignore[reportDeprecated]  pytest fails when defining ProcessorOutput using |
    final,
    runtime_checkable,
)

logger = logging.getLogger(__name__)


_POSITIONAL_ONLY = _ParameterKind.POSITIONAL_ONLY
_POSITIONAL_OR_KEYWORD = _ParameterKind.POSITIONAL_OR_KEYWORD
_VAR_POSITIONAL = _ParameterKind.VAR_POSITIONAL
_KEYWORD_ONLY = _ParameterKind.KEYWORD_ONLY
_VAR_KEYWORD = _ParameterKind.VAR_KEYWORD


ProcessorOutput = Union[Mapping[str, Any], NamedTuple, None]  # type: ignore[reportDeprecated]  # noqa: UP007  otherwise pytest fails


# IProcess protocol cannot be generic because the return type is abstract.
# However, any IProcess can be made generic and return a generic TypedDict.
@runtime_checkable
class IProcess(Protocol):
    process: Callable[..., Mapping[str, Any] | NamedTuple | None] = NotImplemented


class _empty:
    """Marker object for InProcessorParam.default."""


class InMethod(Enum):
    init = 0
    process = 1


@dataclass(frozen=True)
class ProcessorParam(ABC):
    name: str
    annotation: type

    def __eq__(self, other: Any) -> bool:
        return self.__class__ == other.__class__ and self.name == other.name

    def __repr__(self) -> str:
        return self.name + ": " + formatannotation(self.annotation)


@final
@dataclass(frozen=True, slots=True)
class InProcessorParam(ProcessorParam):
    POSITIONAL_ONLY = _POSITIONAL_ONLY
    POSITIONAL_OR_KEYWORD = _POSITIONAL_OR_KEYWORD
    VAR_POSITIONAL = _VAR_POSITIONAL
    KEYWORD_ONLY = _KEYWORD_ONLY
    VAR_KEYWORD = _VAR_KEYWORD

    name: str
    annotation: type | Any
    in_method: InMethod
    kind: _ParameterKind = POSITIONAL_OR_KEYWORD
    default: Any = _empty
    empty: Any = _empty

    @property
    def required(self) -> bool:
        return self.default is self.empty

    @property
    def optional(self) -> bool:
        return not self.required


@final
@dataclass(frozen=True)
class OutProcessorParam(ProcessorParam):
    name: str
    annotation: type

    def to_inparameter(self, in_method: InMethod = InMethod.process) -> InProcessorParam:
        return InProcessorParam(
            self.name,
            self.annotation,
            in_method=in_method,
            default=_empty,
        )


class Annotations:
    """Evaluates annotations of an object's methods."""

    @staticmethod
    def _eval_annotation(module_name: str, annotation: str) -> type:
        module_dict = sys.modules[module_name].__dict__
        return eval(annotation, module_dict)

    @classmethod
    def _signature(
        cls,
        in_method: InMethod,
        method: Callable[..., Any],
        exclude_self: bool = True,
        exclude_var_positional: bool = False,
        exclude_var_keyword: bool = False,
    ) -> dict[str, InProcessorParam]:
        return {
            k: InProcessorParam(p.name, p.annotation, in_method, p.kind, p.default, p.empty)
            for k, p in signature(method, eval_str=True).parameters.items()
            if not (k == "self" and exclude_self)
            and not (p.kind == p.VAR_POSITIONAL and exclude_var_positional)
            and not (p.kind == p.VAR_KEYWORD and exclude_var_keyword)
            and not k == "return"  # "return" key is reserved
        }

    @classmethod
    def get_return_annotation(cls, method: Callable[..., Any]) -> Mapping[str, OutProcessorParam]:
        """Evaluates return annotation given object type and method.

        Object type is needed to load the corresponding module for the evaluation of annotations in
        Python <3.9.

        """
        output = get_annotations(method, eval_str=True)["return"]
        annotations = output.__annotations__ if output else {}
        return {k: OutProcessorParam(k, ann) for k, ann in annotations.items()}

    @classmethod
    def get_processor_signature(
        cls, processor_type: type[IProcess]
    ) -> dict[str, InProcessorParam]:
        # Classes that inherit from Protocol and do not override __init__, have an __init__ set by
        # in Protocol.__init_subclass__ to a function in the typing module.  That function accepts
        # *args and **kwargs, but in runtime, no constructor parameters are allowed.
        # Therefore, if processor_type.__init__.__module__=="typing" we should assume the init
        # signature is empty.
        if getattr(processor_type.__init__, "__module__", None) == "typing":
            init = dict()
        else:
            init = cls._signature(InMethod.init, processor_type)
        proc = cls._signature(InMethod.process, processor_type.process)
        return init | proc
