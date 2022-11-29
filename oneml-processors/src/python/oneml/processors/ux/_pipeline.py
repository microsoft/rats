from __future__ import annotations

from abc import ABC
from collections import Counter
from dataclasses import dataclass
from itertools import chain
from sqlite3 import NotSupportedError
from typing import Any, Generic, Iterable, Mapping, NoReturn, TypeVar, cast, final

from ..dag import DAG, DagNode, InProcessorParam, OutProcessorParam
from ..utils import frozendict

PP = TypeVar("PP", bound=InProcessorParam | OutProcessorParam, covariant=True)
PM = TypeVar("PM", bound="PipelineParam[Any]", covariant=True)
PC = TypeVar("PC", bound="PipelineParamCollection[Any]", covariant=True)
PL = TypeVar("PL", bound="PipelineIO[Any]", covariant=True)


@dataclass(frozen=True)
class PipelineParam(Generic[PP], ABC):
    node: DagNode
    param: PP

    def __post_init__(self) -> None:
        if not isinstance(self.node, DagNode):
            raise ValueError("`node` needs to be `DagNode`.")

    def __contains__(self, other: Any) -> bool:
        return other == self.param.name if isinstance(other, str) else other == self.param

    def __repr__(self) -> str:
        return f"({repr(self.node)}) {repr(self.param)}"

    def decorate(self: PM, name: str) -> PM:
        return self.__class__(self.node.decorate(name), self.param)


@final
@dataclass(frozen=True)
class InParameter(PipelineParam[InProcessorParam]):
    def __post_init__(self) -> None:
        super().__post_init__()
        if not isinstance(self.param, InProcessorParam):
            raise ValueError("`param` needs to be `InProcessorParam`.")

    def __lshift__(self, other: OutParameter) -> tuple[Dependency]:
        if not isinstance(other, OutParameter):
            raise ValueError("Not assinging outputs to inputs.")

        dp = Dependency(self, other)
        return (dp,)


@final
@dataclass(frozen=True)
class OutParameter(PipelineParam[OutProcessorParam]):
    def __post_init__(self) -> None:
        super().__post_init__()
        if not isinstance(self.param, OutProcessorParam):
            raise ValueError("`param` needs to be `OutProcessorParam`.")

    def __rshift__(self, other: InParameter) -> tuple[Dependency]:
        if not isinstance(other, InParameter):
            raise ValueError("Not assinging outputs to inputs.")

        dp = Dependency(other, self)
        return (dp,)


class PipelineParamCollection(frozendict[str, PM], ABC):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        if not all(isinstance(k, str) for k in self):
            raise ValueError("inputs keys be `str`.")

    def __and__(self, other: Mapping[str, Any]) -> NoReturn:
        raise NotImplementedError

    def __or__(self: PC, other: Any) -> PC:
        if set(self) & set(other):
            raise ValueError(f"Keys are repeated and cannot be merged: {set(self) & set(other)}")

        return super().__or__(other)

    def __repr__(self) -> str:
        return "\n".join([repr(param) + "." + space for space, param in self.items()])

    def __sub__(self: PC, other: Iterable[str] | Iterable[PM]) -> PC:
        def get_key(param: PipelineParam[Any]) -> str | None:
            return next(iter(k for k, p in self.items() if p == param), None)

        if all(isinstance(i, str) for i in other):
            return super().__sub__(cast(Iterable[str], other))
        elif all(isinstance(i, PipelineParam) for i in other):
            return super().__sub__(filter(None, map(get_key, cast(Iterable[PM], other))))
        else:
            raise NotSupportedError("`other` needs to be an iterator of `str` or `PipelineParam`.")

    def decorate(self: PC, name: str) -> PC:
        return self.__class__({k: v.decorate(name) for k, v in self.items()})

    def rename(self: PC, names: Mapping[str, str]) -> PC:
        return self.__class__({names.get(k, k): v for k, v in self.items()})


@final
class InCollection(PipelineParamCollection[InParameter]):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        if not all(isinstance(v, InParameter) for v in self.values()):
            raise ValueError("inputs values be `InParameter`.")

    def __lshift__(self, other: OutCollection) -> tuple[Dependency, ...]:
        if not isinstance(other, OutCollection):
            raise ValueError("Dependency assignment only accepts OutCollection's.")

        self_counts = Counter(in_space for in_space in self)
        other_counts = Counter(out_space for out_space in other)
        if len(other_counts) > 1 and self_counts != other_counts:
            raise ValueError("Node names in collections have to match.")

        if any(count > 1 for count in self_counts.values()):
            raise ValueError("Node name collision in collections: not supported.")

        return tuple(
            dependency
            for in_space, in_param in self.items()
            for out_space, out_param in other.items()
            if in_space == out_space or len(other_counts) == 1
            for dependency in in_param << out_param
        )


@final
class OutCollection(PipelineParamCollection[OutParameter]):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        if not all(isinstance(v, OutParameter) for v in self.values()):
            raise ValueError("inputs values be `OutParameter`.")

    def __rshift__(self, other: InCollection) -> tuple[Dependency, ...]:
        if not isinstance(other, InCollection):
            raise ValueError("Dependency assignment only accepts InCollection's.")

        self_counts = Counter(out_space for out_space in self)
        other_counts = Counter(in_space for in_space in other)
        if len(self_counts) > 1 and self_counts != other_counts:
            raise ValueError("Node names in collections have to match.")

        if any(count > 1 for count in self_counts.values()):
            raise ValueError("Node name collision in collections: not supported.")

        return tuple(
            dependency
            for in_space, in_param in other.items()
            for out_space, out_param in self.items()
            if in_space == out_space or len(self_counts) == 1
            for dependency in in_param << out_param
        )


class PipelineIO(frozendict[str, PC], ABC):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        if not all(isinstance(k, str) for k in self._d):
            raise ValueError("inputs keys be `str`.")

    def __and__(self, other: Mapping[str, Any]) -> NoReturn:
        raise NotImplementedError

    def __or__(self: PL, other: Mapping[str, Any]) -> PL:
        un, ix = set(self) | set(other), set(self) & set(other)
        d = {k: self[k] | other[k] if k in ix else self[k] if k in self else other[k] for k in un}
        return self.__class__(d)

    def __sub__(
        self: PL, other: Iterable[str] | Iterable[PC] | Iterable[PipelineParam[Any]]
    ) -> PL:
        def get_key(collection: PipelineParamCollection[Any]) -> str | None:
            return next(iter(k for k, c in self.items() if c == collection), None)

        if all(isinstance(i, str) for i in other):
            return super().__sub__(cast(Iterable[str], other))
        elif all(isinstance(i, PipelineParamCollection) for i in other):
            return super().__sub__(filter(None, map(get_key, cast(Iterable[PC], other))))
        elif all(isinstance(i, PipelineParam) for i in other):
            d = dict(self)
            for k in self:
                d[k] -= other
                if len(d[k]) == 0:
                    del d[k]
            return self.__class__(d)
        else:
            raise NotSupportedError(
                "`other` needs to be an iterator of `str`, "
                + "`PipelineParamCollection` or `PipelineParam`."
            )

    def decorate(self: PL, name: str) -> PL:
        return self.__class__({k: v.decorate(name) for k, v in self.items()})

    def rename(self: PL, names: Mapping[str, str]) -> PL:
        return self.__class__({k: v.rename(names) for k, v in self.items()})


class PipelineInput(PipelineIO[InCollection]):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        if not all(isinstance(v, InCollection) for v in self.values()):
            raise ValueError("all `inputs` values need to be of `InCollection` type.")

    def __lshift__(self, other: PipelineOutput) -> tuple[Dependency, ...]:
        if not isinstance(other, PipelineOutput):
            raise ValueError("Dependency assignment only accepts `PipelineOutput`.")

        intersecting_keys = set(self) & set(other)
        return tuple(chain.from_iterable(self[k] << other[k] for k in intersecting_keys))


class PipelineOutput(PipelineIO[OutCollection]):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        if not all(isinstance(v, OutCollection) for v in self.values()):
            raise ValueError("all `outputs` values need to be of `OutCollection` type.")

    def __rshift__(self, other: PipelineInput) -> tuple[Dependency, ...]:
        if not isinstance(other, PipelineInput):
            raise ValueError("Dependency assignment only accepts `PipelineInput`.")

        intersecting_keys = set(self) & set(other)
        return tuple(chain.from_iterable(self[k] >> other[k] for k in intersecting_keys))


@final
@dataclass(frozen=True)
class Dependency:
    in_param: PipelineParam[InProcessorParam]
    out_param: PipelineParam[OutProcessorParam]

    def __repr__(self) -> str:
        return f"{repr(self.in_param)} <- {repr(self.out_param)}"

    def decorate(self, in_name: str, out_name: str) -> Dependency:
        return self.__class__(self.in_param.decorate(in_name), self.out_param.decorate(out_name))


@dataclass(frozen=True)
class Pipeline:
    name: str
    dag: DAG = DAG()
    inputs: PipelineInput = PipelineInput()
    outputs: PipelineOutput = PipelineOutput()

    def __len__(self) -> int:
        return len(self.dag)

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or len(self.name) == 0:
            raise ValueError("Missing pipeline name.")
        if not isinstance(self.dag, DAG):
            raise ValueError(f"{self.dag} needs to be an instance of DAG.")
        if not isinstance(self.inputs, PipelineInput):
            raise ValueError("`inputs` need to be of `PipelineInput` type.")
        if not isinstance(self.outputs, PipelineOutput):
            raise ValueError("`outputs` needs to be of `PipelineOutput` type.")

    def __lshift__(self, other: Pipeline) -> tuple[Dependency, ...]:
        if not isinstance(other, Pipeline):
            raise ValueError("Dependency assignment only accepts another `Pipeline`.")

        return self.inputs << other.outputs

    def __rshift__(self, other: Pipeline) -> tuple[Dependency, ...]:
        if not isinstance(other, Pipeline):
            raise ValueError("Dependency assignment only accepts `Pipeline`.")

        return self.outputs >> other.inputs

    def decorate(self, name: str) -> Pipeline:
        inputs, outputs = self.inputs.decorate(name), self.outputs.decorate(name)
        return Pipeline(name, self.dag.decorate(name), inputs, outputs)

    def rename(self, names: Mapping[str, str]) -> Pipeline:
        inputs, outputs = self.inputs.rename(names), self.outputs.rename(names)
        return Pipeline(self.name, self.dag, inputs, outputs)
