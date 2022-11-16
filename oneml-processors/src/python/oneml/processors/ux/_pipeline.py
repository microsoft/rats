from __future__ import annotations

from abc import ABC
from collections import Counter
from dataclasses import dataclass
from typing import Any, ItemsView, Iterator, KeysView, Mapping, TypeAlias, ValuesView, final

from ..dag._dag import DAG, DagNode
from ..dag._processor import InProcessorParam, OutProcessorParam, ProcessorParam
from ..utils._frozendict import frozendict


@final
@dataclass(frozen=True)
class Dependency:
    in_param: InParameter
    out_param: OutParameter

    def __repr__(self) -> str:
        return f"{repr(self.in_param)} <- {repr(self.out_param)}"

    def decorate(self, in_name: str, out_name: str) -> Dependency:
        return self.__class__(self.in_param.decorate(in_name), self.out_param.decorate(out_name))


@dataclass(frozen=True)
class PipelineParam(ABC):
    node: DagNode
    param: ProcessorParam

    def __post_init__(self) -> None:
        if not isinstance(self.node, DagNode):
            raise ValueError("node has to be DagNode.")
        if not isinstance(self.param, ProcessorParam):
            raise ValueError("param has to be ProcessorParam.")

    def __contains__(self, other: Any) -> bool:
        return other == self.param.name if isinstance(other, str) else other == self.param

    def __repr__(self) -> str:
        return f"({repr(self.node)}) {repr(self.param)}"

    def decorate(self, name: str) -> PipelineParam:
        return self.__class__(self.node.decorate(name), self.param)


@final
@dataclass(frozen=True)
class InParameter(PipelineParam):
    param: InProcessorParam

    def __post_init__(self) -> None:
        if not isinstance(self.param, InProcessorParam):
            raise ValueError("param has to be InProcessorParam.")
        super().__post_init__()

    def decorate(self, name: str) -> InParameter:
        return self.__class__(self.node.decorate(name), self.param)

    def __lshift__(self, other: OutParameter) -> tuple[Dependency]:
        if not isinstance(other, OutParameter):
            raise ValueError("Not assinging outputs to inputs.")

        dp = Dependency(self, other)
        return (dp,)


@final
@dataclass(frozen=True)
class OutParameter(PipelineParam):
    param: OutProcessorParam

    def __post_init__(self) -> None:
        if not isinstance(self.param, OutProcessorParam):
            raise ValueError("param has to be OutProcessorParam.")
        super().__post_init__()

    def decorate(self, name: str) -> OutParameter:
        return self.__class__(self.node.decorate(name), self.param)

    def __rshift__(self, other: InParameter) -> tuple[Dependency]:
        if not isinstance(other, InParameter):
            raise ValueError("Not assinging outputs to inputs.")

        dp = Dependency(other, self)
        return (dp,)


@dataclass(frozen=True)
class PipelineParamCollection(ABC):
    collection: Mapping[str, PipelineParam]

    def __contains__(self, other: Any) -> bool:
        return other in self.collection if isinstance(other, str) else False

    def __getattr__(self, key: str) -> PipelineParam:
        return self.collection[key]

    def __getitem__(self, key: str) -> PipelineParam:
        return self.collection[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self.collection)

    def __len__(self) -> int:
        return len(self.collection)

    def __repr__(self) -> str:
        return "\n".join([repr(param) + "." + group for group, param in self.collection.items()])

    def keys(self) -> KeysView[str]:
        return self.collection.keys()

    def decorate(self, name: str) -> PipelineParamCollection:
        return self.__class__({k: v.decorate(name) for k, v in self.collection.items()})

    def values(self) -> ValuesView[PipelineParam]:
        return self.collection.values()

    def items(self) -> ItemsView[str, PipelineParam]:
        return self.collection.items()


@final
@dataclass(frozen=True, init=False)
class InParamCollection(PipelineParamCollection):
    collection: dict[str, InParameter]

    def __post_init__(self) -> None:
        if not all(isinstance(v, InParameter) for v in self.collection.values()):
            raise ValueError("Collection values have to be InParameter's.")

    def __getattr__(self, key: str) -> InParameter:
        return self.collection[key]

    def __getitem__(self, key: str) -> InParameter:
        return self.collection[key]

    def decorate(self, name: str) -> InParamCollection:
        return self.__class__({k: v.decorate(name) for k, v in self.collection.items()})

    def values(self) -> ValuesView[InParameter]:
        return self.collection.values()

    def items(self) -> ItemsView[str, InParameter]:
        return self.collection.items()

    def __lshift__(self, other: OutParamCollection) -> tuple[Dependency, ...]:
        if not isinstance(other, OutParamCollection):
            raise ValueError("Dependency assignment only accepts OutParamCollection's.")

        self_counts = Counter(in_space for in_space in self.collection)
        other_counts = Counter(out_space for out_space in other.collection)
        if len(other_counts) > 1 and self_counts != other_counts:
            raise ValueError("Node names in collections have to match.")

        if any(count > 1 for count in self_counts.values()):
            raise ValueError("Node name collision in collections: not supported.")

        return tuple(
            dependency
            for in_space, in_param in self.collection.items()
            for out_space, out_param in other.collection.items()
            if in_space == out_space or len(other_counts) == 1
            for dependency in in_param << out_param
        )


@final
@dataclass(frozen=True)
class OutParamCollection(PipelineParamCollection):
    collection: dict[str, OutParameter]

    def __post_init__(self) -> None:
        if not all(isinstance(v, OutParameter) for v in self.collection.values()):
            raise ValueError("Collection values have to be OutParameter's.")

    def __getattr__(self, key: str) -> OutParameter:
        return self.collection[key]

    def __getitem__(self, key: str) -> OutParameter:
        return self.collection[key]

    def decorate(self, name: str) -> OutParamCollection:
        return self.__class__({k: v.decorate(name) for k, v in self.collection.items()})

    def values(self) -> ValuesView[OutParameter]:
        return self.collection.values()

    def items(self) -> ItemsView[str, OutParameter]:
        return self.collection.items()

    def __rshift__(self, other: InParamCollection) -> tuple[Dependency, ...]:
        if not isinstance(other, InParamCollection):
            raise ValueError("Dependency assignment only accepts InParamCollection's.")

        self_counts = Counter(out_space for out_space in self.collection)
        other_counts = Counter(in_space for in_space in other.collection)
        if len(self_counts) > 1 and self_counts != other_counts:
            raise ValueError("Node names in collections have to match.")

        if any(count > 1 for count in self_counts.values()):
            raise ValueError("Node name collision in collections: not supported.")

        return tuple(
            dependency
            for in_space, in_param in other.collection.items()
            for out_space, out_param in self.collection.items()
            if in_space == out_space or len(self_counts) == 1
            for dependency in in_param << out_param
        )


PipelineInput: TypeAlias = frozendict[str, InParamCollection]
PipelineOutput: TypeAlias = frozendict[str, OutParamCollection]


@dataclass(frozen=True)
class Pipeline:
    name: str
    dag: DAG = DAG()
    inputs: PipelineInput = frozendict()
    outputs: PipelineOutput = frozendict()

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or len(self.name) == 0:
            raise ValueError("Missing pipeline name.")
        if not isinstance(self.dag, DAG):
            raise ValueError(f"{self.dag} must be an instance of DAG.")
        if not all(
            isinstance(k, str) and isinstance(v, InParamCollection) for k, v in self.inputs.items()
        ):
            raise ValueError("inputs should be `frozendict[str, InParamCollection`.")
        if not all(
            isinstance(k, str) and isinstance(v, OutParamCollection)
            for k, v in self.outputs.items()
        ):
            raise ValueError("outputs should be `frozendict[str, OutParamCollection`.")

    def __contains__(self, node: DagNode) -> bool:
        return node in self.dag

    def decorate(self, name: str) -> Pipeline:
        inputs: PipelineInput = frozendict({k: v.decorate(name) for k, v in self.inputs.items()})
        output: PipelineOutput = frozendict({k: v.decorate(name) for k, v in self.outputs.items()})
        return Pipeline(name, self.dag.decorate(name), inputs, output)
