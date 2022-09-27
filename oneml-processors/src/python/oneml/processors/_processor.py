from __future__ import annotations

import inspect
import logging
import sys
from abc import abstractmethod
from enum import Enum
from functools import cached_property
from inspect import Parameter
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Generic,
    Mapping,
    Protocol,
    Sequence,
    Type,
    TypedDict,
    TypeVar,
    get_args,
)

if TYPE_CHECKING:
    from ._client import DataClient

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=Mapping[str, Any], covariant=True)  # output mapping of processors
TI = TypeVar("TI", covariant=True)  # generic input types for processor
TO = TypeVar("TO", contravariant=True)  # generic output types for processor


class DataArg(Generic[TI]):
    def __init__(self, key: str) -> None:
        if not isinstance(key, str) or len(key) == 0:
            raise ValueError("key must be string of length > 0.")

        super().__init__()
        self._key = key

    def __bool__(self) -> bool:
        return True

    def __eq__(self, arg: object) -> bool:
        # ignore annotation when comparing
        return self._key == arg.key if isinstance(arg, DataArg) else False

    def __hash__(self) -> int:
        return hash(self._key)  # ignore annotation when hashing

    def __repr__(self) -> str:
        return self.key + ": " + str(self.annotation)

    @property
    def key(self) -> str:
        return self._key

    @cached_property
    def annotation(self) -> TI:
        annotation = get_args(getattr(self, "__orig_class__"))
        return annotation[0] if annotation else Any


class IProcessor(Protocol[T]):  # Processor is covariant
    @abstractmethod
    def process(self) -> T:  # https://peps.python.org/pep-0692/
        ...


class IDefineArgVars(Protocol):
    args: Sequence[str] = ()
    kwargs: Sequence[str] = ()


class IArgVarsProcessor(IProcessor[T], IDefineArgVars):
    pass


class DependencyKind(Enum):
    STANDARD = 0  # one to one correspondence between processors outputs and inputs
    SEQUENCE = 1  # many to one correspondences
    MAPPING = 2
    NAMEDTUPLE = 3
    DATACLASS = 4


# C.arrays <- A.x
# C.arrays <- B.x

# C.mydict.x1 <- A.x1
# C.mydict.y1 <- B.y1
# mydict = {x: A.x, y: B.y}

# TypedDict("output", {"arr1": int, ..., "arr5": int,  "Y": int})
# TypedDict("output", {"arrays": TypedDict("arrays", {"arr1": int, ..., "arr5": Array}), "Y": int})


class Provider(Generic[T]):
    _processor_type: Type[IProcessor[T]]
    _config: Mapping[str, Any]

    def __init__(
        self, processor_type: Type[IProcessor[T]], config: Mapping[str, Any] = {}
    ) -> None:
        super().__init__()
        self._processor_type = processor_type
        self._config = config
        self._validate_config()

    def _validate_config(self) -> None:
        in_sig = ProcessorInput.signature(self.processor_type.__init__)
        if not all(key in in_sig for key in self._config.keys()):
            raise ValueError("Config has entries not accepted by Processor.")

    def get_processor(self, data_client: DataClient) -> IProcessor[T]:
        sig = Annotations.get_signature_parameters(self.processor_type.__init__)
        inputs = data_client.get_formatted_args(sig, exclude=tuple(self.config.keys()))
        positional_args, keyword_args = inputs.values()
        return self.processor_type(*positional_args, **self.config, **keyword_args)

    def execute(self, data_client: DataClient) -> None:
        processor = self.get_processor(data_client)
        sig = Annotations.get_signature_parameters(self.processor_type.process)
        inputs = data_client.get_formatted_args(sig, exclude=tuple(self.config.keys()))
        positional_args, keyword_args = inputs.values()
        output = processor.process(*positional_args, **keyword_args)
        for key, val in output.items():
            data_client.save(key, val)

    @property
    def processor_type(self) -> Type[IProcessor[T]]:
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

    @staticmethod
    def get_signature_parameters(
        method: Callable[..., Any],
        exclude_self: bool = True,
        exclude_var_positional: bool = False,
        exclude_var_keyword: bool = False,
    ) -> dict[str, inspect.Parameter]:
        return {
            k: param
            for k, param in inspect.signature(method, eval_str=True).parameters.items()
            if not (k == "self" and exclude_self)
            and not (param.kind == param.VAR_POSITIONAL and exclude_var_positional)
            and not (param.kind == param.VAR_KEYWORD and exclude_var_keyword)
            and not k == "return"  # "return" key is reserved
        }

    # @classmethod
    # def get_signature_annotations(
    #     cls,
    #     method: Callable[..., Any],
    #     exclude_self: bool = True,
    #     exclude_var_positional: bool = True,
    #     exclude_var_keyword: bool = True,
    # ) -> dict[str, type]:
    #     """Evaluates annotation given object type and method.

    #     Object type is needed to load the corresponding module for the evaluation of annotations in
    #     Python <3.9.

    #     """
    #     if sys.version_info >= (3, 10):
    #         sig = inspect.signature(method, eval_str=True)
    #         return {
    #             k: param.annotation
    #             for k, param in sig.parameters.items()
    #             if not (k == "self" and exclude_self)
    #             and not (param.kind == param.VAR_POSITIONAL and exclude_var_positional)
    #             and not (param.kind == param.VAR_KEYWORD and exclude_var_keyword)
    #             and not k == "return"  # "return" key is reserved
    #         }
    #     else:
    #         sig = inspect.signature(method)
    #         return {
    #             k: param.annotation
    #             if not isinstance(param.annotation, str)
    #             else cls._eval_annotation(method.__module__, param.annotation)
    #             for k, param in sig.parameters.items()
    #             if not (k == "self" and exclude_self)
    #             and not (param.kind == param.VAR_POSITIONAL and exclude_var_positional)
    #             and not (param.kind == param.VAR_KEYWORD and exclude_var_keyword)
    #         }

    @classmethod
    def get_return_annotation(cls, method: Callable[..., Any]) -> type:
        """Evaluates return annotation given object type and method.

        Object type is needed to load the corresponding module for the evaluation of annotations in
        Python <3.9.

        """
        if sys.version_info >= (3, 10):
            none = TypedDict("none", {})
            annotations = inspect.get_annotations(method, eval_str=True)
            return annotations.pop("return", none)
        else:
            ra = inspect.signature(method).return_annotation
            return ra if isinstance(ra, type) else cls._eval_annotation(method.__module__, ra)


class ProcessorInput:
    """Processor's input signature."""

    @staticmethod
    def signature(method: Callable[..., Any]) -> Mapping[str, Parameter]:
        """Computes processor's signature via `inspect.signature`."""
        return Annotations.get_signature_parameters(method)
        # return {k: DataArg[ann](k) for k, ann in annotations.items()}  # type: ignore

    @classmethod
    def signature_from_provider(cls, provider: Provider[T]) -> Mapping[str, Parameter]:
        """Returns Processor's input signature given its provider."""
        init_sig = Annotations.get_signature_parameters(
            provider.processor_type.__init__, exclude_var_positional=True, exclude_var_keyword=True
        )
        process_sig = Annotations.get_signature_parameters(
            provider.processor_type.process, exclude_var_positional=True, exclude_var_keyword=True
        )
        if sys.version_info >= (3, 9):
            merged_sigs = init_sig | process_sig
        else:
            merged_sigs = {**init_sig, **process_sig}
        return {k: v for k, v in merged_sigs.items() if k not in provider.config}
        # return {
        #     k: DataArg[v](k)  # type: ignore[valid-type]
        #     for k, v in merged_sigs.items()
        #     if k not in provider.config
        # }


class ProcessorOutput:
    """Processor's output signature."""

    @staticmethod
    def signature(method: Callable[..., Any]) -> Mapping[str, DataArg[Any]]:
        """Computes processor's return annotation signature via `inspect.signature`."""
        return_mapping = Annotations.get_return_annotation(method)
        return {k: DataArg[ann](k) for k, ann in return_mapping.__annotations__.items()}  # type: ignore[valid-type]  # noqa: E501

    @classmethod
    def signature_from_provider(cls, provider: Provider[T]) -> Mapping[str, DataArg[Any]]:
        """Returns Processor's output signature given its provider."""
        return cls.signature(provider.processor_type.process)
