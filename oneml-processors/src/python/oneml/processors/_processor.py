from __future__ import annotations

import inspect
import logging
import sys
from abc import abstractmethod
from functools import cached_property
from typing import Any, Dict, Generic, Mapping, Protocol, Type, TypedDict, TypeVar, get_args

from oneml.pipelines.session import (
    PipelineNodeDataClient,
    PipelineNodeInputDataClient,
    PipelinePort,
)

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=Mapping[str, Any], covariant=True)  # output mapping of processors
TI = TypeVar("TI", covariant=True)  # generic input types for processor
TO = TypeVar("TO", contravariant=True)  # generic output types for processor


class DataArg(PipelinePort[TI]):
    def __repr__(self) -> str:
        return self.key + ": " + str(self.annotation)

    @cached_property
    def annotation(self) -> TI:
        annotation = get_args(getattr(self, "__orig_class__"))
        return annotation[0] if annotation else Any


class Processor(Protocol[T]):  # Processor is covariant
    @abstractmethod
    def process(self) -> T:  # https://peps.python.org/pep-0692/
        ...


class Provider(Generic[T]):
    _processor_type: Type[Processor[T]]
    _config: Mapping[str, Any]

    def __init__(self, processor_type: Type[Processor[T]], config: Mapping[str, Any] = {}) -> None:
        super().__init__()
        self._processor_type = processor_type
        self._config = config
        self._validate_config()

    def _validate_config(self) -> None:
        in_sig = ProcessorInput.signature(self.processor_type, "__init__")
        if not all(key in in_sig for key in self._config.keys()):
            raise ValueError("Config has entries not accepted by Processor.")

    def get_processor(self, data_client: PipelineNodeInputDataClient) -> Processor[T]:
        init_sig = dict(ProcessorInput.signature(self.processor_type, "__init__"))
        input: Dict[str, Any] = {
            k: data_client.get_data(PipelinePort[arg.annotation](arg.key))  # type: ignore[name-defined]  # noqa: E501
            for k, arg in init_sig.items()
            if k not in self.config
        }
        return self.processor_type(**self.config, **input)

    def execute(
        self,
        input_client: PipelineNodeInputDataClient,
        publish_client: PipelineNodeDataClient,
    ) -> None:
        proc_sig = ProcessorInput.signature(self.processor_type, "process")
        input: Dict[str, Any] = {
            k: input_client.get_data(PipelinePort[arg.annotation](arg.key))  # type: ignore[name-defined]  # noqa: E501
            for k, arg in proc_sig.items()
        }
        processor = self.get_processor(input_client)
        output = processor.process(**input)
        for key, val in output.items():
            publish_client.publish_data(PipelinePort(key), val)

    @property
    def processor_type(self) -> Type[Processor[T]]:
        return self._processor_type

    @property
    def config(self) -> Mapping[str, Any]:
        return self._config


class Annotations:
    """Evaluates annotations of an object's methods.

    Supports Python <3.9 and 3.10.

    """

    @staticmethod
    def _eval_annotation(obj_type: type, annotation: str) -> type:
        module_name = obj_type.__module__
        module = sys.modules[module_name]
        module_dict = module.__dict__
        return eval(annotation, module_dict)

    @classmethod
    def get_annotations(
        cls,
        obj_type: type,
        method: str,
        exclude_self: bool = True,
        exclude_var_positional: bool = True,
        exclude_var_keyword: bool = True,
    ) -> Dict[str, type]:
        """Evaluates annotation given object type and method.

        Object type is needed to load the corresponding module for the evaluation of annotations in
        Python <3.9.

        """
        if sys.version_info >= (3, 10):
            annotations = inspect.get_annotations(getattr(obj_type, method), eval_str=True)
            annotations.pop("return", None)  # "return" key is reserved
            return annotations
        else:
            sig = inspect.signature(getattr(obj_type, method))
            return {
                k: param.annotation
                if not isinstance(param.annotation, str)
                else cls._eval_annotation(obj_type, param.annotation)
                for k, param in sig.parameters.items()
                if not (k == "self" and exclude_self)
                and not (param.kind == param.VAR_POSITIONAL and exclude_var_positional)
                and not (param.kind == param.VAR_KEYWORD and exclude_var_keyword)
            }

    @classmethod
    def get_return_annotation(cls, obj_type: type, method: str) -> type:
        """Evaluates return annotation given object type and method.

        Object type is needed to load the corresponding module for the evaluation of annotations in
        Python <3.9.

        """
        if sys.version_info >= (3, 10):
            none = TypedDict("none", {})
            annotations = inspect.get_annotations(getattr(obj_type, method), eval_str=True)
            return annotations.pop("return", none)
        else:
            ra = inspect.signature(getattr(obj_type, method)).return_annotation
            return ra if isinstance(ra, type) else cls._eval_annotation(obj_type, ra)


class ProcessorInput:
    """Processor's input signature."""

    @staticmethod
    def signature(processor_type: Type[Processor[T]], method: str) -> Mapping[str, DataArg[Any]]:
        """Computes processor's signature via `inspect.signature`."""
        annotations = Annotations.get_annotations(processor_type, method)
        return {k: DataArg[v](k) for k, v in annotations.items()}  # type: ignore

    @classmethod
    def signature_from_provider(cls, provider: Provider[T]) -> Mapping[str, DataArg[Any]]:
        """Returns Processor's input signature given its provider."""
        init_sig = Annotations.get_annotations(provider.processor_type, "__init__")
        process_sig = Annotations.get_annotations(provider.processor_type, "process")
        if sys.version_info >= (3, 9):
            merged_sigs = init_sig | process_sig
        else:
            merged_sigs = {**init_sig, **process_sig}
        return {
            k: DataArg[v](k)  # type: ignore[valid-type]
            for k, v in merged_sigs.items()
            if k not in provider.config
        }


class ProcessorOutput:
    """Processor's output signature."""

    @staticmethod
    def signature(processor_type: Type[Processor[T]]) -> Mapping[str, DataArg[Any]]:
        """Computes processor's return annotation signature via `inspect.signature`."""
        return_mapping = Annotations.get_return_annotation(processor_type, "process")
        return {k: DataArg[ann](k) for k, ann in return_mapping.__annotations__.items()}  # type: ignore[valid-type]  # noqa: E501

    @classmethod
    def signature_from_provider(cls, provider: Provider[T]) -> Mapping[str, DataArg[Any]]:
        """Returns Processor's output signature given its provider."""
        return cls.signature(provider.processor_type)
