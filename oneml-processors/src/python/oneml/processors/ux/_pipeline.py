from __future__ import annotations

from abc import ABC
from dataclasses import dataclass
from itertools import chain
from sqlite3 import NotSupportedError
from typing import Any, Generic, Iterable, Mapping, NoReturn, TypeVar, final

from ..dag import DAG, DagNode, InProcessorParam, OutProcessorParam
from ..utils import frozendict, orderedset

PP = TypeVar("PP", bound=InProcessorParam | OutProcessorParam, covariant=True)
PM = TypeVar("PM", bound="PipelineParam[Any]", covariant=True)
PE = TypeVar("PE", bound="ParamCollectionEntry[Any]", covariant=True)
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

    def __lshift__(self, other: OutParameter) -> Dependency:
        if not isinstance(other, OutParameter):
            raise ValueError("Not assinging outputs to inputs.")

        return Dependency(self, other)


@final
@dataclass(frozen=True)
class OutParameter(PipelineParam[OutProcessorParam]):
    def __post_init__(self) -> None:
        super().__post_init__()
        if not isinstance(self.param, OutProcessorParam):
            raise ValueError("`param` needs to be `OutProcessorParam`.")

    def __rshift__(self, other: InParameter) -> Dependency:
        if not isinstance(other, InParameter):
            raise ValueError("Not assinging outputs to inputs.")

        return Dependency(other, self)


class ParamCollectionEntry(orderedset[PM], ABC):
    def decorate(self: PE, name: str) -> PE:
        return self.__class__(param.decorate(name) for param in self)


@final
class InCollectionEntry(ParamCollectionEntry[InParameter]):
    def __init__(self, __iterable: Iterable[InParameter]) -> None:
        super().__init__(__iterable)
        if not all(isinstance(in_param, InParameter) for in_param in self):
            raise ValueError("All elements of `InCollectionEntry` must be `InParameter`s.")

    def __lshift__(self, other: OutCollectionEntry) -> tuple[Dependency, ...]:
        if not isinstance(other, OutCollectionEntry):
            raise ValueError("Not assinging outputs to inputs.")

        return tuple(in_param << other[0] for in_param in self)


@final
class OutCollectionEntry(ParamCollectionEntry[OutParameter]):
    def __init__(self, __iterable: Iterable[OutParameter]) -> None:
        super().__init__(__iterable)
        if len(self) != 1 and not isinstance(self[0], OutParameter):
            raise ValueError("`OutCollectionEntry` must have a single `OutParameter` element.")

    def __or__(self, other: Any) -> NoReturn:
        raise ValueError("`OutCollectionEntry` cannot be merged.")

    def __rshift__(self, other: InCollectionEntry) -> tuple[Dependency, ...]:
        if not isinstance(other, InCollectionEntry):
            raise ValueError("Not assinging outputs to inputs.")

        return tuple(self[0] >> in_param for in_param in other)


class PipelineParamCollection(frozendict[str, PE], ABC):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        if not all(isinstance(k, str) for k in self):
            raise ValueError("Input keys need to be `str` types.")

    def __and__(self, other: Mapping[str, Any]) -> NoReturn:
        raise NotImplementedError

    def __or__(self: PC, other: Any) -> PC:
        new_d = dict(self) | dict(other) | {k: self[k] | other[k] for k in set(self) & set(other)}
        return self.__class__(new_d)

    def __repr__(self) -> str:
        return "\n".join([repr(p) + "." + entry for entry, params in self.items() for p in params])

    def __sub__(self: PC, other: Iterable[str | PE | PM]) -> PC:
        def get_key(v: str | PE | PM) -> str | None:
            if isinstance(v, str):
                return v
            elif isinstance(v, ParamCollectionEntry):
                return next(iter(k for k, e in self.items() if v == e), None)
            elif isinstance(v, PipelineParam):
                return next(iter(k for k, params in self.items() for p in params if p == v), None)
            else:
                raise NotSupportedError(
                    "`other` needs to be an iterator of `str`, "
                    + "`PipelineParamEntry` or `PipelineParam`."
                )

        return super().__sub__(filter(None, map(get_key, other)))

    def decorate(self: PC, name: str) -> PC:
        return self.__class__({k: entry.decorate(name) for k, entry in self.items()})

    def rename(self: PC, names: Mapping[str, str]) -> PC:
        return self.__class__({names.get(k, k): entry for k, entry in self.items()})


@final
class InCollection(PipelineParamCollection[InCollectionEntry]):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        if not all(isinstance(entry, InCollectionEntry) for entry in self.values()):
            raise ValueError("Input values need to be `InCollectionEntry` types.")

    def __lshift__(self, other: OutCollection) -> tuple[Dependency, ...]:
        if not isinstance(other, OutCollection):
            raise ValueError("Dependency assignment only accepts OutCollection.")

        if len(other) > 1 and set(self) != set(other):
            raise ValueError("Node names in collections have to match.")

        return tuple(
            dependency
            for in_entryname, in_entry in self.items()
            for out_entryname, out_entry in other.items()
            if in_entryname == out_entryname or len(other) == 1
            for dependency in in_entry << out_entry
        )


@final
class OutCollection(PipelineParamCollection[OutCollectionEntry]):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        if not all(isinstance(entry, OutCollectionEntry) for entry in self.values()):
            raise ValueError("Inputs values need to be `OutCollectionEntry` types.")

    def __rshift__(self, other: InCollection) -> tuple[Dependency, ...]:
        if not isinstance(other, InCollection):
            raise ValueError("Dependency assignment only accepts InCollection's.")

        if len(self) > 1 and set(self) != set(other):
            raise ValueError("Node names in collections have to match.")

        return tuple(
            dependency
            for in_entryname, in_entry in other.items()
            for out_entryname, out_entry in self.items()
            if in_entryname == out_entryname or len(self) == 1
            for dependency in out_entry >> in_entry
        )


class PipelineIO(frozendict[str, PC], ABC):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        if not all(isinstance(k, str) for k in self._d):
            raise ValueError("inputs keys be `str`.")

    def __and__(self, other: Mapping[str, Any]) -> NoReturn:
        raise NotImplementedError

    def __or__(self: PL, other: Mapping[str, Any]) -> PL:
        d = dict(self) | dict(other) | {k: self[k] | other[k] for k in set(self) & set(other)}
        return self.__class__(d)

    def __sub__(self: PL, other: Iterable[str | PC | PE | PM]) -> PL:
        def get_key(val: str | PC | PE | PM) -> str | None:
            if isinstance(val, str):
                return val
            elif isinstance(val, PipelineParamCollection):
                return next(iter(k for k, c in self.items() if c == val), None)
            elif not (isinstance(val, ParamCollectionEntry) or isinstance(val, PipelineParam)):
                raise NotSupportedError(
                    "`other` needs to be an iterator of `str`, `PipelineParamCollection`, "
                    + "`ParamCollectionEntry` or `PipelineParam`."
                )
            return None

        d = dict(super().__sub__(filter(None, map(get_key, other))))
        for val in other:
            if isinstance(val, ParamCollectionEntry) or isinstance(val, PipelineParam):
                for k in tuple(d):
                    d[k] -= (val,)
                    if len(d[k]) == 0:
                        del d[k]

        return self.__class__(d)

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
    in_param: InParameter
    out_param: OutParameter

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
