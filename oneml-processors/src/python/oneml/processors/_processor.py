from __future__ import annotations

import logging
import sys
from dataclasses import dataclass
from enum import Enum
from inspect import Parameter, get_annotations, signature
from typing import TYPE_CHECKING, Any, Callable, Mapping, Protocol, Sequence, Type

if TYPE_CHECKING:
    from ._client import DataClient

logger = logging.getLogger(__name__)


# IProcessor protocol cannot be generic because the return type is abstract.
# However, any IProcessor can be made generic and return a generic TypedDict.
class IProcessor(Protocol):
    process: Callable[..., Mapping[str, Any]] = NotImplemented


class IDefineGatherVars(Protocol):
    sequence_vars: Sequence[str] = ()
    mapping_vars: Sequence[str] = ()


class IGatherVarsProcessor(IProcessor, IDefineGatherVars):
    pass


@dataclass(frozen=True)
class OutParameter:
    name: str
    annotation: type


class GatherVarKind(Enum):
    STANDARD = 0  # one to one correspondence between processors outputs and inputs
    SEQUENCE = 1  # many to one correspondences
    MAPPING = 2
    NAMEDTUPLE = 3
    DATACLASS = 4


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
    ) -> dict[str, Parameter]:
        if sys.version_info >= (3, 10):
            return {
                k: param
                for k, param in signature(method, eval_str=True).parameters.items()
                if not (k == "self" and exclude_self)
                and not (param.kind == param.VAR_POSITIONAL and exclude_var_positional)
                and not (param.kind == param.VAR_KEYWORD and exclude_var_keyword)
                and not k == "return"  # "return" key is reserved
            }
        else:
            return {
                k: param
                if not isinstance(param.annotation, str)
                else param.replace(
                    annotation=cls._eval_annotation(method.__module__, param.annotation)
                )
                for k, param in signature(method).parameters.items()
                if not (k == "self" and exclude_self)
                and not (param.kind == param.VAR_POSITIONAL and exclude_var_positional)
                and not (param.kind == param.VAR_KEYWORD and exclude_var_keyword)
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
