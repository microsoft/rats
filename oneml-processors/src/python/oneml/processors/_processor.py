from __future__ import annotations

import logging
import sys
from dataclasses import dataclass
from enum import Enum
from inspect import _ParameterKind, get_annotations, signature
from typing import Any, Callable, Hashable, Mapping, Protocol, final

from ._frozendict import MappingProtocol

logger = logging.getLogger(__name__)


_POSITIONAL_ONLY = _ParameterKind.POSITIONAL_ONLY
_POSITIONAL_OR_KEYWORD = _ParameterKind.POSITIONAL_OR_KEYWORD
_VAR_POSITIONAL = _ParameterKind.VAR_POSITIONAL
_KEYWORD_ONLY = _ParameterKind.KEYWORD_ONLY
_VAR_KEYWORD = _ParameterKind.VAR_KEYWORD


# IProcess protocol cannot be generic because the return type is abstract.
# However, any IProcess can be made generic and return a generic TypedDict.
class IProcess(Protocol):
    process: Callable[..., Mapping[str, Any]] = NotImplemented


class IGetParams(MappingProtocol[str, Any], Hashable, Protocol):
    """Hashable mapping (protocol) for retrieving parameters to construct & execute an IProcess."""


class _empty:
    """Marker object for InParameter.empty."""


class InMethod(Enum):
    init = 0
    process = 1


@final
@dataclass(frozen=True, slots=True)
class InParameter:
    POSITIONAL_ONLY = _POSITIONAL_ONLY
    POSITIONAL_OR_KEYWORD = _POSITIONAL_OR_KEYWORD
    VAR_POSITIONAL = _VAR_POSITIONAL
    KEYWORD_ONLY = _KEYWORD_ONLY
    VAR_KEYWORD = _VAR_KEYWORD

    name: str
    annotation: Any
    in_method: InMethod
    kind: _ParameterKind = POSITIONAL_OR_KEYWORD
    default: Any = _empty
    empty: Any = _empty


@final
@dataclass(frozen=True)
class OutParameter:
    name: str
    annotation: type
    empty: Any = _empty

    def to_inparameter(self, in_method: InMethod = InMethod.process) -> InParameter:
        return InParameter(
            self.name,
            self.annotation,
            in_method=in_method,
            default=self.empty,
            empty=self.empty,
        )


class Annotations:
    """Evaluates annotations of an object's methods.

    Supports Python <3.9 and 3.10.

    """

    @staticmethod
    def _eval_annotation(module_name: str, annotation: str) -> type:
        module_dict = sys.modules[module_name].__dict__
        return eval(annotation, module_dict)

    @classmethod
    def signature(
        cls,
        method: Callable[..., Any],
        exclude_self: bool = True,
        exclude_var_positional: bool = False,
        exclude_var_keyword: bool = False,
    ) -> dict[str, InParameter]:
        in_method = InMethod.process if method.__name__ == "process" else InMethod.init
        if sys.version_info >= (3, 10):
            return {
                k: InParameter(p.name, p.annotation, in_method, p.kind, p.default, p.empty)
                for k, p in signature(method, eval_str=True).parameters.items()
                if not (k == "self" and exclude_self)
                and not (p.kind == p.VAR_POSITIONAL and exclude_var_positional)
                and not (p.kind == p.VAR_KEYWORD and exclude_var_keyword)
                and not k == "return"  # "return" key is reserved
            }
        else:
            return {
                k: InParameter(p.name, p.annotation, in_method, p.kind, p.default, p.empty)
                if not isinstance(p.annotation, str)
                else InParameter(
                    p.name,
                    cls._eval_annotation(method.__module__, p.annotation),
                    p.kind,
                    p.default,
                    p.empty,
                )
                for k, p in signature(method).parameters.items()
                if not (k == "self" and exclude_self)
                and not (p.kind == p.VAR_POSITIONAL and exclude_var_positional)
                and not (p.kind == p.VAR_KEYWORD and exclude_var_keyword)
                and not k == "return"  # "return" key is reserved
            }

    @classmethod
    def get_return_annotation(cls, method: Callable[..., Any]) -> Mapping[str, OutParameter]:
        """Evaluates return annotation given object type and method.

        Object type is needed to load the corresponding module for the evaluation of annotations in
        Python <3.9.

        """
        if sys.version_info >= (3, 10):
            output = get_annotations(method, eval_str=True)["return"]
        else:
            ra = signature(method).return_annotation
            output = ra if isinstance(ra, type) else cls._eval_annotation(method.__module__, ra)
        annotations = output.__annotations__ if output else {}
        return {k: OutParameter(k, ann) for k, ann in annotations.items()}

    @classmethod
    def get_processor_signature(cls, processor_type: type[IProcess]) -> dict[str, InParameter]:
        # Classes that inherit from Protocol and do not override __init__, have an __init__ set by
        # Protocol.__init_subclass__ to typing._no_init_or_replace_init.  On the first
        # invokation of that __init__, it replaces the class's __init__ with whatever the __mro__
        # says.
        # _no_init_or_replace_init does not have the correct signature, whereas after calling it
        # the class does have the correct signature.
        # If all this applies to processor_type, then the following will successfully trigger the
        # __init__ replacement mechanism and the class would have the correct signature.
        # If it doesn't then either it is not a Protocol, or it is a Protocol but provides its own
        # __init__.  The following instanciation might fail, but it does not matter.
        try:
            _ = processor_type()
        except Exception:
            pass
        init = cls.signature(processor_type)
        proc = cls.signature(processor_type.process)
        return {**init, **proc} if sys.version_info < (3, 10) else init | proc
