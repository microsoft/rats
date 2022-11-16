from __future__ import annotations

from abc import ABC
from collections import Counter
from dataclasses import dataclass
from typing import Any, ItemsView, Iterator, KeysView, Mapping, TypeAlias, ValuesView, final

from .._frozendict import frozendict
from .._pipeline import Pipeline, PNode
from .._processor import InParameter, OutParameter, Parameter


@final
@dataclass(frozen=True)
class Dependency:
    in_param: InWorkflowParam
    out_param: OutWorkflowParam

    def __repr__(self) -> str:
        return f"{repr(self.in_param)} <- {repr(self.out_param)}"

    def decorate(self, in_name: str, out_name: str) -> Dependency:
        return self.__class__(self.in_param.decorate(in_name), self.out_param.decorate(out_name))


@dataclass(frozen=True)
class WorkflowParam(ABC):
    node: PNode
    param: Parameter

    def __post_init__(self) -> None:
        if not isinstance(self.node, PNode):
            raise ValueError("node has to be PNode.")
        if not isinstance(self.param, Parameter):
            raise ValueError("param has to be Parameter.")

    def __contains__(self, other: Any) -> bool:
        return other == self.param.name if isinstance(other, str) else other == self.param

    def __repr__(self) -> str:
        return f"({repr(self.node)}) {repr(self.param)}"

    def decorate(self, name: str) -> WorkflowParam:
        return self.__class__(self.node.decorate(name), self.param)


@final
@dataclass(frozen=True)
class InWorkflowParam(WorkflowParam):
    param: InParameter

    def __post_init__(self) -> None:
        if not isinstance(self.param, InParameter):
            raise ValueError("param has to be InParameter.")
        super().__post_init__()

    def decorate(self, name: str) -> InWorkflowParam:
        return self.__class__(self.node.decorate(name), self.param)

    def __lshift__(self, other: OutWorkflowParam) -> tuple[Dependency]:
        if not isinstance(other, OutWorkflowParam):
            raise ValueError("Not assinging outputs to inputs.")

        dp = Dependency(self, other)
        return (dp,)


@final
@dataclass(frozen=True)
class OutWorkflowParam(WorkflowParam):
    param: OutParameter

    def __post_init__(self) -> None:
        if not isinstance(self.param, OutParameter):
            raise ValueError("param has to be OutParameter.")
        super().__post_init__()

    def decorate(self, name: str) -> OutWorkflowParam:
        return self.__class__(self.node.decorate(name), self.param)

    def __rshift__(self, other: InWorkflowParam) -> tuple[Dependency]:
        if not isinstance(other, InWorkflowParam):
            raise ValueError("Not assinging outputs to inputs.")

        dp = Dependency(other, self)
        return (dp,)


@dataclass(frozen=True)
class WorkflowParamCollection(ABC):
    collection: Mapping[str, WorkflowParam]

    def __contains__(self, other: Any) -> bool:
        return other in self.collection if isinstance(other, str) else False

    def __getattr__(self, key: str) -> WorkflowParam:
        return self.collection[key]

    def __getitem__(self, key: str) -> WorkflowParam:
        return self.collection[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self.collection)

    def __len__(self) -> int:
        return len(self.collection)

    def __repr__(self) -> str:
        return "\n".join([repr(param) + "." + group for group, param in self.collection.items()])

    def keys(self) -> KeysView[str]:
        return self.collection.keys()

    def decorate(self, name: str) -> WorkflowParamCollection:
        return self.__class__({k: v.decorate(name) for k, v in self.collection.items()})

    def values(self) -> ValuesView[WorkflowParam]:
        return self.collection.values()

    def items(self) -> ItemsView[str, WorkflowParam]:
        return self.collection.items()


@final
@dataclass(frozen=True, init=False)
class InWorkflowParamCollection(WorkflowParamCollection):
    collection: dict[str, InWorkflowParam]

    def __post_init__(self) -> None:
        if not all(isinstance(v, InWorkflowParam) for v in self.collection.values()):
            raise ValueError("Collection values have to be InWorkflowParam's.")

    def __getattr__(self, key: str) -> InWorkflowParam:
        return self.collection[key]

    def __getitem__(self, key: str) -> InWorkflowParam:
        return self.collection[key]

    def decorate(self, name: str) -> InWorkflowParamCollection:
        return self.__class__({k: v.decorate(name) for k, v in self.collection.items()})

    def values(self) -> ValuesView[InWorkflowParam]:
        return self.collection.values()

    def items(self) -> ItemsView[str, InWorkflowParam]:
        return self.collection.items()

    def __lshift__(self, other: OutWorkflowParamCollection) -> tuple[Dependency, ...]:
        if not isinstance(other, OutWorkflowParamCollection):
            raise ValueError("Dependency assignment only accepts OutWorkflowParamCollection's.")

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
class OutWorkflowParamCollection(WorkflowParamCollection):
    collection: dict[str, OutWorkflowParam]

    def __post_init__(self) -> None:
        if not all(isinstance(v, OutWorkflowParam) for v in self.collection.values()):
            raise ValueError("Collection values have to be OutWorkflowParam's.")

    def __getattr__(self, key: str) -> OutWorkflowParam:
        return self.collection[key]

    def __getitem__(self, key: str) -> OutWorkflowParam:
        return self.collection[key]

    def decorate(self, name: str) -> OutWorkflowParamCollection:
        return self.__class__({k: v.decorate(name) for k, v in self.collection.items()})

    def values(self) -> ValuesView[OutWorkflowParam]:
        return self.collection.values()

    def items(self) -> ItemsView[str, OutWorkflowParam]:
        return self.collection.items()

    def __rshift__(self, other: InWorkflowParamCollection) -> tuple[Dependency, ...]:
        if not isinstance(other, InWorkflowParamCollection):
            raise ValueError("Dependency assignment only accepts InWorkflowParamCollection's.")

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


WorkflowInput: TypeAlias = frozendict[str, InWorkflowParamCollection]
WorkflowOutput: TypeAlias = frozendict[str, OutWorkflowParamCollection]


@dataclass(frozen=True)
class Workflow:
    name: str
    pipeline: Pipeline = Pipeline()
    inputs: WorkflowInput = frozendict()
    outputs: WorkflowOutput = frozendict()

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or len(self.name) == 0:
            raise ValueError("Missing workflow name.")
        if not isinstance(self.pipeline, Pipeline):
            raise ValueError(f"{self.pipeline} must be an instance of Pipeline.")
        if not all(
            isinstance(k, str) and isinstance(v, InWorkflowParamCollection)
            for k, v in self.inputs.items()
        ):
            raise ValueError("inputs should be `frozendict[str, InWorkflowParamCollection`.")
        if not all(
            isinstance(k, str) and isinstance(v, OutWorkflowParamCollection)
            for k, v in self.outputs.items()
        ):
            raise ValueError("outputs should be `frozendict[str, OutWorkflowParamCollection`.")

    def __contains__(self, node: PNode) -> bool:
        return node in self.pipeline

    def decorate(self, name: str) -> Workflow:
        inputs: WorkflowInput = frozendict({k: v.decorate(name) for k, v in self.inputs.items()})
        output: WorkflowOutput = frozendict({k: v.decorate(name) for k, v in self.outputs.items()})
        return Workflow(name, self.pipeline.decorate(name), inputs, output)
