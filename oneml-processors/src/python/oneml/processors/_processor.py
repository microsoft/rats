from __future__ import annotations

import logging
import sys
from dataclasses import dataclass
from inspect import _ParameterKind, get_annotations, signature
from typing import TYPE_CHECKING, Any, Callable, Mapping, Protocol, Type, final

if TYPE_CHECKING:
    from ._client import DataClient

logger = logging.getLogger(__name__)

_POSITIONAL_ONLY = _ParameterKind.POSITIONAL_ONLY
_POSITIONAL_OR_KEYWORD = _ParameterKind.POSITIONAL_OR_KEYWORD
_VAR_POSITIONAL = _ParameterKind.VAR_POSITIONAL
_KEYWORD_ONLY = _ParameterKind.KEYWORD_ONLY
_VAR_KEYWORD = _ParameterKind.VAR_KEYWORD


class _empty:
    """Marker object for InParameter.empty."""


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
    kind: _ParameterKind = POSITIONAL_OR_KEYWORD
    default: Any = _empty
    empty: Any = _empty


@final
@dataclass(frozen=True)
class OutParameter:
    name: str
    annotation: type


# IProcessor protocol cannot be generic because the return type is abstract.
# However, any IProcessor can be made generic and return a generic TypedDict.
class IProcessor(Protocol):
    process: Callable[..., Mapping[str, Any]] = NotImplemented


class Provider:
    _processor_type: Type[IProcessor]
    _config: Mapping[str, Any]

    def __init__(self, processor_type: Type[IProcessor], config: Mapping[str, Any] = {}) -> None:
        super().__init__()
        self._processor_type = processor_type
        self._config = config
        self._validate_config()

    def _validate_config(self) -> None:
        in_sig = Annotations.signature(self.processor_type.__init__)
        if not all(key in in_sig for key in self._config.keys()):
            raise ValueError("Config has entries not accepted by Processor.")

    def get_processor(self, data_client: DataClient) -> IProcessor:
        sig = Annotations.signature(self.processor_type.__init__)
        pos_args, kw_args = data_client.load_parameters(sig, exclude=tuple(self.config.keys()))
        return self.processor_type(*pos_args, **self.config, **kw_args)

    def execute(self, data_client: DataClient) -> None:
        processor = self.get_processor(data_client)
        sig = Annotations.signature(self.processor_type.process)
        pos_args, kw_args = data_client.load_parameters(sig, exclude=tuple(self.config.keys()))
        output = processor.process(*pos_args, **kw_args)
        for key, val in output.items():
            data_client.save(key, val)

    @property
    def processor_type(self) -> Type[IProcessor]:
        return self._processor_type

    @property
    def config(self) -> Mapping[str, Any]:
        return self._config


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
        if sys.version_info >= (3, 10):
            return {
                k: InParameter(p.name, p.annotation, p.kind, p.default, p.empty)
                for k, p in signature(method, eval_str=True).parameters.items()
                if not (k == "self" and exclude_self)
                and not (p.kind == p.VAR_POSITIONAL and exclude_var_positional)
                and not (p.kind == p.VAR_KEYWORD and exclude_var_keyword)
                and not k == "return"  # "return" key is reserved
            }
        else:
            return {
                k: InParameter(p.name, p.annotation, p.kind, p.default, p.empty)
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
