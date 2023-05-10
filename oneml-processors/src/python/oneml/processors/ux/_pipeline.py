from __future__ import annotations

from abc import ABC
from dataclasses import dataclass
from itertools import chain
from typing import Any, Generic, Iterable, Mapping, TypeAlias, TypeVar, final, overload

from omegaconf import MISSING

from ..dag import DAG, DagNode, InProcessorParam, OutProcessorParam
from ..utils import frozendict, orderedset
from ._ops import (
    CollectionDependencyOp,
    Dependency,
    EntryDependencyOp,
    IOCollectionDependencyOp,
    PipelineDependencyOp,
)

PP = TypeVar("PP", bound=InProcessorParam | OutProcessorParam, covariant=True)
PM = TypeVar("PM", bound="PipelineParam[Any]", covariant=True)
PE = TypeVar("PE", bound="ParamEntry[Any]", covariant=True)
PC = TypeVar("PC", bound="ParamCollection[Any]", covariant=True)
PL = TypeVar("PL", bound="IOCollections[Any]", covariant=True)
PCi = TypeVar("PCi", bound="ParamCollection[Any]")
PLi = TypeVar("PLi", bound="IOCollections[Any]")


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

    @property
    def required(self) -> bool:
        return self.param.required

    @property
    def optional(self) -> bool:
        return not self.required


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


class ParamEntry(orderedset[PM], ABC):
    def decorate(self: PE, name: str) -> PE:
        return self.__class__(param.decorate(name) for param in self)


@final
class InEntry(ParamEntry[InParameter]):
    def __init__(self, __iterable: Iterable[InParameter] = ()) -> None:
        super().__init__(__iterable)
        if not all(isinstance(in_param, InParameter) for in_param in self):
            raise ValueError("All elements of `InEntry` must be `InParameter`s.")

    def __lshift__(self, other: OutEntry) -> EntryDependencyOp:
        if not isinstance(other, OutEntry):
            raise ValueError("Cannot assign to `InEntry`; `other` must be `OutEntry`.")

        return EntryDependencyOp(self, other)

    @property
    def required(self) -> bool:
        return any((p.required for p in self))

    @property
    def optional(self) -> bool:
        return not self.required


@final
class OutEntry(ParamEntry[OutParameter]):
    def __init__(self, __iterable: Iterable[OutParameter] = ()) -> None:
        super().__init__(__iterable)
        if not all(isinstance(out_param, OutParameter) for out_param in self):
            raise ValueError("All elements of `OutEntry` must be `OutParameter`s.")

    def __rshift__(self, other: InEntry) -> EntryDependencyOp:
        if not isinstance(other, InEntry):
            raise ValueError("Cannot assign to `OutEntry`; `other` must be `InEntry`.")

        return EntryDependencyOp(other, self)


class ParamCollection(frozendict[str, PE], ABC):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        if not all(isinstance(k, str) for k in self):
            raise ValueError("Input keys need to be `str` types.")

    def __or__(self: PC, other: Mapping[str, Any]) -> PC:
        if not isinstance(other, Mapping):
            raise ValueError("`other` needs to be a `Mapping`.")
        new_d = dict(self) | dict(other) | {k: self[k] | other[k] for k in set(self) & set(other)}
        return self.__class__(new_d)

    def __repr__(self) -> str:
        return "\n".join([repr(p) + "." + entry for entry, params in self.items() for p in params])

    def __sub__(self: PC, other: Iterable[str | PE | PM]) -> PC:
        def get_key(v: str | PE | PM) -> str | None:
            if isinstance(v, str):
                return v
            elif isinstance(v, ParamEntry):
                return next(iter(k for k, e in self.items() if v == e), None)
            elif isinstance(v, PipelineParam):
                return next(iter(k for k, params in self.items() for p in params if p == v), None)
            else:
                raise ValueError(
                    "`other` needs to be an iterator of `str`, "
                    + "`PipelineParamEntry` or `PipelineParam`."
                )

        return super().__sub__(filter(None, map(get_key, other)))

    def decorate(self: PC, name: str) -> PC:
        return self.__class__({k: entry.decorate(name) for k, entry in self.items()})

    def rename(self: PC, names: Mapping[str, str]) -> PC:
        if any(k.count(".") > 0 for k in names.values()):
            raise ValueError("New names cannot contain dots.")

        d = self
        for ko, kn in names.items():
            d -= (ko,)
            d |= {kn: self[ko]}

        return d


@final
class Inputs(ParamCollection[InEntry]):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        if not all(isinstance(entry, InEntry) for entry in self.values()):
            raise ValueError("Input values need to be `InEntry` types.")

    def __lshift__(self, other: Outputs) -> CollectionDependencyOp:
        if not isinstance(other, Outputs):
            raise ValueError("Cannot assign to `Inputs`; `other` must be `Outputs`.")

        if set(self) != set(other):
            raise ValueError("Node names in collections have to match.")

        return CollectionDependencyOp(self, other)

    def get_required(self) -> Inputs:
        """Returns the subset of the inputs that are required."""
        return Inputs(filter(lambda t: t[1].required, self.items()))


@final
class Outputs(ParamCollection[OutEntry]):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        if not all(isinstance(entry, OutEntry) for entry in self.values()):
            raise ValueError("Inputs values need to be `OutEntry` types.")

    def __rshift__(self, other: Inputs) -> CollectionDependencyOp:
        if not isinstance(other, Inputs):
            raise ValueError("Cannot assign to `Outputs`; `other` must be `Inputs`.")

        if set(self) != set(other):
            raise ValueError("Node names in collections have to match.")

        return CollectionDependencyOp(other, self)


class IOCollections(frozendict[str, PC], ABC):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        if not all(isinstance(k, str) for k in self._d):
            raise ValueError("inputs keys be `str`.")
        if not all(isinstance(e, ParamCollection) for e in self.values()):
            raise ValueError("inputs values be `ParamCollection`.")

    def __or__(self: PL, other: Mapping[str, Any]) -> PL:
        if not isinstance(other, Mapping):
            raise ValueError("`other` needs to be a `Mapping`.")
        d = dict(self) | dict(other) | {k: self[k] | other[k] for k in set(self) & set(other)}
        return self.__class__(d)

    def __sub__(self: PL, other: Iterable[str | PC | PE | PM]) -> PL:
        def get_key(val: str | PC | PE | PM) -> str | None:
            if isinstance(val, str):
                return val
            elif isinstance(val, ParamCollection):
                return next(iter(k for k, c in self.items() if c == val), None)
            elif not (isinstance(val, ParamEntry) or isinstance(val, PipelineParam)):
                raise ValueError(
                    "`other` needs to be an iterator of `str`, `ParamCollection`, "
                    + "`ParamEntry` or `PipelineParam`."
                )
            return None

        d = dict(super().__sub__(filter(None, map(get_key, other))))
        for v in other:
            if isinstance(v, str) and v.count(".") == 1 and v.split(".")[0] in d:
                v0, v1 = v.split(".")
                d[v0] -= (v1,)
                if len(d[v0]) == 0:
                    del d[v0]
            elif isinstance(v, ParamEntry) or isinstance(v, PipelineParam):
                for k in tuple(d):
                    d[k] -= (v,)
                    if len(d[k]) == 0:
                        del d[k]

        return self.__class__(d)

    def decorate(self: PL, name: str) -> PL:
        return self.__class__({k: v.decorate(name) for k, v in self.items()})

    def rename(self: PL, names: Mapping[str, str]) -> PL:
        if any(k.count(".") > 1 for k in chain.from_iterable(names.items())):
            raise ValueError("Names cannot contain more than single dot in keys or values.")

        d: dict[str, PC] = dict(self)
        for ok, nk in names.items():  # old key, new key
            ok_split, nk_split = ok.split(".", 1), nk.split(".", 1)
            ok1, ok2 = ok_split if len(ok_split) == 2 else (ok, "")
            nk1, nk2 = nk_split if len(nk_split) == 2 else (nk, "")
            if ok2 and nk2:  # ParamCollection.ParamEntry -> ParamCollection.ParamEntry
                d[ok1] = self[ok1] - (ok2,)  # removes ParamEntry from ParamCollection
                if len(d[ok1]) == 0:
                    del d[ok1]
                d[nk1] = d.get(nk1, self[ok1].__class__()) | {nk2: self[ok1][ok2]}
            elif not ok2 and not nk2:  # ParamCollection -> ParamCollection
                del d[ok]
                d[nk] = self.get(nk, self[ok].__class__()) | self[ok]
            else:
                raise ValueError("Not supported.")

        return self.__class__(d)


InCollection: TypeAlias = Inputs
OutCollection: TypeAlias = Outputs


class InCollections(IOCollections[InCollection]):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        if not all(isinstance(v, Inputs) for v in self.values()):
            raise ValueError("all `inputs` values need to be `Inputs` type.")

    def __lshift__(self, other: OutCollections) -> IOCollectionDependencyOp:
        if not isinstance(other, OutCollections):
            raise ValueError("Dependency assignment only accepts `OutCollections`.")

        return IOCollectionDependencyOp(self, other)

    def get_required(self) -> InCollections:
        """Returns the subset of the inputs that are required."""
        return InCollections(
            filter(
                lambda t: len(t[1]) > 0,
                ((name, collection.get_required()) for name, collection in self.items()),
            )
        )


class OutCollections(IOCollections[OutCollection]):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        if not all(isinstance(v, Outputs) for v in self.values()):
            raise ValueError("all `outputs` values need to be `Outputs` type.")

    def __rshift__(self, other: InCollections) -> IOCollectionDependencyOp:
        if not isinstance(other, InCollections):
            raise ValueError("Dependency assignment only accepts `InCollections`.")

        return IOCollectionDependencyOp(other, self)


@dataclass
class PipelineConf:
    name: str = MISSING


class Pipeline:
    _name: str
    _dag: DAG = DAG()
    _config: PipelineConf = PipelineConf()
    _inputs: Inputs = Inputs()
    _outputs: Outputs = Outputs()
    _in_collections: InCollections = InCollections()
    _out_collections: OutCollections = OutCollections()

    @overload
    def __init__(
        self,
        *,
        other: Pipeline,
        config: PipelineConf | None = None,
    ) -> None:
        ...

    @overload
    def __init__(
        self,
        *,
        name: str,
        dag: DAG,
        config: PipelineConf,
        inputs: Inputs = Inputs(),
        outputs: Outputs = Outputs(),
        in_collections: InCollections = InCollections(),
        out_collections: OutCollections = OutCollections(),
    ) -> None:
        ...

    def __init__(
        self,
        name: str | None = None,
        dag: DAG | None = None,
        config: PipelineConf | None = None,
        inputs: Inputs | None = None,
        outputs: Outputs | None = None,
        in_collections: InCollections | None = None,
        out_collections: OutCollections | None = None,
        other: Pipeline | None = None,
    ) -> None:
        if other is None:
            if not isinstance(name, str) or len(name) == 0:
                raise ValueError("Missing pipeline name.")
            if not isinstance(dag, DAG):
                raise ValueError(f"{dag} needs to be an instance of DAG.")
            if inputs is None:
                inputs = Inputs()
            if not isinstance(inputs, Inputs):
                raise ValueError("`inputs` need to be of `Inputs` type.")
            if outputs is None:
                outputs = Outputs()
            if not isinstance(outputs, Outputs):
                raise ValueError("`outputs` needs to be of `Outputs` type.")
            if in_collections is None:
                in_collections = InCollections()
            if not isinstance(in_collections, InCollections):
                raise ValueError("`in_collections` need to be of `InCollections` type.")
            if out_collections is None:
                out_collections = OutCollections()
            if not isinstance(out_collections, OutCollections):
                raise ValueError("`out_collections` needs to be of `OutCollections` type.")
            if not isinstance(config, PipelineConf):
                raise ValueError("`config` needs to be of `PipelineConf` type.")
        else:
            if not isinstance(other, Pipeline):
                raise ValueError("When `other` is given, it should be a Pipeline.")
            spurious_params = []
            if name is not None:
                spurious_params.append("name")
            if dag is not None:
                spurious_params.append("dag")
            if inputs is not None:
                spurious_params.append("inputs")
            if outputs is not None:
                spurious_params.append("outputs")
            if in_collections is not None:
                spurious_params.append("in_collections")
            if out_collections is not None:
                spurious_params.append("out_collections")
            if len(spurious_params) > 1:
                raise ValueError(
                    "When `other` is given, the following params should not be given: "
                    f"{spurious_params}."
                )
            name = other._name
            inputs = other._inputs
            outputs = other._outputs
            in_collections = other._in_collections
            out_collections = other._out_collections
            dag = other._dag
            if config is None:
                config = other._config

        self._name = name
        self._inputs = inputs
        self._outputs = outputs
        self._in_collections = in_collections
        self._out_collections = out_collections
        self._dag = dag
        self._config = config

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Pipeline):
            return self._dag == other._dag
        return False

    def __hash__(self) -> int:
        return hash(self._dag)

    def __len__(self) -> int:
        return len(self._dag)

    def __repr__(self) -> str:
        return f"{self.name}({self._dag})"

    def __lshift__(self, other: Pipeline) -> PipelineDependencyOp:
        if not isinstance(other, Pipeline):
            raise ValueError("Dependency assignment only accepts another `Pipeline`.")

        return PipelineDependencyOp(self, other)

    def __rshift__(self, other: Pipeline) -> PipelineDependencyOp:
        if not isinstance(other, Pipeline):
            raise ValueError("Dependency assignment only accepts `Pipeline`.")

        return PipelineDependencyOp(other, self)

    def decorate(self, name: str) -> Pipeline:
        dag = self._dag.decorate(name)
        inputs = self.inputs.decorate(name)
        outputs = self.outputs.decorate(name)
        in_collections = self.in_collections.decorate(name)
        out_collections = self.out_collections.decorate(name)
        return Pipeline(
            name=name,
            dag=dag,
            config=self._config,
            inputs=inputs,
            outputs=outputs,
            in_collections=in_collections,
            out_collections=out_collections,
        )

    def _rename(self, names: Mapping[str, str], collection: PCi, io: PLi) -> tuple[PCi, PLi]:
        if any(k.count(".") > 1 for k in chain.from_iterable(names.items())):
            raise ValueError("Names cannot contain more than single dot in keys or values.")

        for ok, nk in names.items():  # old key, new key
            ok_split, nk_split = ok.split(".", 1), nk.split(".", 1)
            ok1, ok2 = ok_split if len(ok_split) == 2 else (ok, "")
            nk1, nk2 = nk_split if len(nk_split) == 2 else (nk, "")
            if (ok1 in io and ok2 in io[ok1] and nk2) or (ok1 in io and not ok2 and not nk2):
                # ParamCollection.ParamEntry -> ParamCollection.ParamEntry
                io = io.rename({ok: nk})  # or ParamCollection -> ParamCollection
            elif ok1 in collection and not ok2 and not nk2:  # ParamEntry -> ParamEntry
                collection = collection.rename({ok: nk})
            elif ok1 in collection and not ok2 and nk2:  # ParamEntry -> ParamCollection.ParamEntry
                io |= {nk1: io.get(nk1, collection.__class__()) | {nk2: collection[ok1]}}
                collection -= (collection[ok1],)
            elif ok1 in io and ok2 in io[ok1]:  # ParamCollection.ParamEntry -> ParamEntry
                collection |= {nk: io[ok1][ok2]}
                io -= (io[ok1][ok2],)
            else:
                raise ValueError(f"Cannot rename {ok} to {nk}; non existing {ok} or wrong format.")

        return collection, io

    def rename_inputs(self, names: Mapping[str, str]) -> Pipeline:
        new_PC, new_PL = self._rename(names, self.inputs, self.in_collections)
        return Pipeline(
            name=self.name,
            dag=self._dag,
            config=self._config,
            inputs=new_PC,
            outputs=self.outputs,
            in_collections=new_PL,
            out_collections=self.out_collections,
        )

    def rename_outputs(self, names: Mapping[str, str]) -> Pipeline:
        new_PC, new_PL = self._rename(names, self.outputs, self.out_collections)
        return Pipeline(
            name=self.name,
            dag=self._dag,
            config=self._config,
            inputs=self.inputs,
            outputs=new_PC,
            in_collections=self.in_collections,
            out_collections=new_PL,
        )

    @property
    def name(self) -> str:
        return self._name

    @property
    def inputs(self) -> Inputs:
        return self._inputs

    @property
    def outputs(self) -> Outputs:
        return self._outputs

    @property
    def in_collections(self) -> InCollections:
        return self._in_collections

    @property
    def out_collections(self) -> OutCollections:
        return self._out_collections

    @property
    def required_inputs(self) -> Inputs:
        return self.inputs.get_required()

    @property
    def required_in_collections(self) -> InCollections:
        return self.in_collections.get_required()
