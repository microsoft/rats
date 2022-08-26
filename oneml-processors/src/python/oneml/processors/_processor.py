import sys
from abc import abstractmethod
from dataclasses import dataclass
from inspect import _empty, signature
from itertools import chain
from typing import Any, Generic, Mapping, Protocol, Type, TypeVar

from omegaconf import DictConfig

from oneml.pipelines.building import IPipelineSessionExecutable
from oneml.pipelines.session import PipelineSessionClient

from ._frozendict import FrozenDict

T = TypeVar("T", bound=Mapping[str, Any], covariant=True)  # output mapping of processors
D = TypeVar("D", covariant=True)


@dataclass(frozen=True)
class PipelineData(Generic[D]):
    name: str

    def __repr__(self) -> str:
        return self.name


class Processor(Protocol[T]):  # Processor is covariant
    @abstractmethod
    def process(self) -> T:
        ...


class Provider(IPipelineSessionExecutable, Generic[T]):
    _processor_type: Type[Processor[T]]

    def __init__(self, processor_type: Type[Processor[T]], config: DictConfig) -> None:
        super().__init__()
        self._processor_type = processor_type
        self._config = config  # hashable? frozen?

    def execute(self, session_client: PipelineSessionClient) -> None:
        pass

    @property
    def processor_type(self) -> Type[Processor[T]]:
        return self._processor_type


class EvalFromModule:
    @staticmethod
    def eval_annotation(processor_type: Type[Processor[T]], annotation: str) -> type:
        module_name = processor_type.__module__
        module = sys.modules[module_name]
        module_dict = module.__dict__
        return eval(annotation, module_dict)


class ProcessorInput:
    @staticmethod
    def signature(processor_type: Type[Processor[T]]) -> FrozenDict[str, Type[Any]]:
        init_items = signature(processor_type.__init__).parameters.items()
        process_items = signature(processor_type.process).parameters.items()
        in_sig = {
            k: EvalFromModule.eval_annotation(processor_type, v.annotation)
            for k, v in chain(init_items, process_items)
            if k != "self" and v.annotation != _empty
        }
        return FrozenDict(in_sig)

    @classmethod
    def signature_from_provider(cls, provider: Provider[T]) -> FrozenDict[str, Type[Any]]:
        return cls.signature(provider.processor_type)


class ProcessorOutput:
    @staticmethod
    def signature(processor_type: Type[Processor[T]]) -> FrozenDict[str, Type[Any]]:
        return_annotation = signature(processor_type.process).return_annotation
        return_mapping = EvalFromModule.eval_annotation(processor_type, return_annotation)
        return FrozenDict(getattr(return_mapping, "__annotations__", {}))

    @classmethod
    def signature_from_provider(cls, provider: Provider[T]) -> FrozenDict[str, Type[Any]]:
        return cls.signature(provider.processor_type)
