from __future__ import annotations

from abc import ABC
from dataclasses import dataclass
from itertools import chain
from typing import Any, Generic, Iterable, Mapping, NoReturn, cast, final, overload

from typing_extensions import Self, TypeVar

from ..dag import DAG, DagNode, InProcessorParam, OutProcessorParam
from ..utils import NamedCollection, orderedset
from ._ops import (
    CollectionDependencyOp,
    Dependency,
    EntryDependencyOp,
    IOCollectionDependencyOp,
    PipelineDependencyOp,
)
from ._verification import verify_pipeline_integrity

T = TypeVar("T")
PP = TypeVar("PP", bound=InProcessorParam | OutProcessorParam, covariant=True)
PM = TypeVar("PM", bound="PipelineParam[Any, Any]", covariant=True)
PE = TypeVar("PE", bound="ParamEntry[Any]", covariant=True)
PC = TypeVar("PC", bound="ParamCollection[Any]", covariant=True)
PL = TypeVar("PL", bound="IOCollections[Any]", covariant=True)
PCi = TypeVar("PCi", bound="ParamCollection[Any]")
PLi = TypeVar("PLi", bound="IOCollections[Any]")


@dataclass(frozen=True)
class PipelineParam(Generic[PP, T], ABC):
    node: DagNode
    param: PP

    def __post_init__(self) -> None:
        if not isinstance(self.node, DagNode):
            raise ValueError("`node` needs to be `DagNode`.")

    def __contains__(self, other: Any) -> bool:
        return other == self.param.name if isinstance(other, str) else other == self.param

    def __repr__(self) -> str:
        return f"({repr(self.node)}) {repr(self.param)}"

    def decorate(self, name: str) -> Self:
        return self.__class__(self.node.decorate(name), self.param)


@final
@dataclass(frozen=True)
class InParameter(PipelineParam[InProcessorParam, T]):
    def __post_init__(self) -> None:
        super().__post_init__()
        if not isinstance(self.param, InProcessorParam):
            raise ValueError("`param` needs to be `InProcessorParam`.")

    def __lshift__(self, other: OutParameter[T]) -> Dependency[T]:
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
class OutParameter(PipelineParam[OutProcessorParam, T]):
    def __post_init__(self) -> None:
        super().__post_init__()
        if not isinstance(self.param, OutProcessorParam):
            raise ValueError("`param` needs to be `OutProcessorParam`.")

    def __rshift__(self, other: InParameter[T]) -> Dependency[T]:
        if not isinstance(other, InParameter):
            raise ValueError("Not assinging outputs to inputs.")

        return Dependency(other, self)


class ParamEntry(orderedset[PM], ABC):
    def __repr__(self) -> str:
        ann = str(self[0].param.annotation).replace("<class '", "").replace("'>", "")
        return f"{self.__class__.__name__}[{ann}]"

    def decorate(self, name: str) -> Self:
        return self.__class__(param.decorate(name) for param in self)


@final
class InEntry(ParamEntry[InParameter[T]]):
    def __init__(self, __iterable: Iterable[InParameter[T]] = ()) -> None:
        super().__init__(__iterable)
        if not all(isinstance(in_param, InParameter) for in_param in self):
            raise ValueError("All elements of `InEntry` must be `InParameter`s.")

    def __lshift__(self, other: OutEntry[T]) -> EntryDependencyOp[T]:
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
class OutEntry(ParamEntry[OutParameter[T]]):
    def __init__(self, __iterable: Iterable[OutParameter[T]] = ()) -> None:
        super().__init__(__iterable)
        if not all(isinstance(out_param, OutParameter) for out_param in self):
            raise ValueError("All elements of `OutEntry` must be `OutParameter`s.")

    def __rshift__(self, other: InEntry[T]) -> EntryDependencyOp[T]:
        if not isinstance(other, InEntry):
            raise ValueError("Cannot assign to `OutEntry`; `other` must be `InEntry`.")

        return EntryDependencyOp(other, self)


class ParamCollection(NamedCollection[PE], ABC):
    def decorate(self, name: str) -> Self:
        return self.__class__({k: entry.decorate(name) for k, entry in self._asdict().items()})


class InCollection(ParamCollection[InEntry[T]]):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        if not all(isinstance(entry, InEntry) for entry in self._asdict().values()):
            raise ValueError("Input values need to be `InEntry` types.")

    def __lshift__(self, other: OutCollection[T]) -> CollectionDependencyOp[T]:
        if not isinstance(other, OutCollection):
            raise ValueError("Cannot assign to `Inputs`; `other` must be `Outputs`.")

        if set(self) != set(other):
            raise ValueError("Node names in collections have to match.")

        return CollectionDependencyOp(self, other)

    def get_required(self) -> InCollection[T]:
        """Returns the subset of the inputs that are required."""
        return InCollection(filter(lambda t: t[1].required, self._asdict().items()))


class OutCollection(ParamCollection[OutEntry[T]]):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        if not all(isinstance(entry, OutEntry) for entry in self._asdict().values()):
            raise ValueError("Inputs values need to be `OutEntry` types.")

    def __rshift__(self, other: InCollection[T]) -> CollectionDependencyOp[T]:
        if not isinstance(other, InCollection):
            raise ValueError("Cannot assign to `Outputs`; `other` must be `Inputs`.")

        if set(self) != set(other):
            raise ValueError("Node names in collections have to match.")

        return CollectionDependencyOp(other, self)


Inputs = InCollection[Any]
Outputs = OutCollection[Any]


class NoInputs(InCollection[Any]):
    def __getattr__(self, key: str) -> NoReturn:
        raise KeyError(f"Inputs has no attribute {key}.")


class NoOutputs(OutCollection[Any]):
    def __getattr__(self, key: str) -> NoReturn:
        raise KeyError(f"Outputs has no attribute {key}.")


class IOCollections(NamedCollection[PC], ABC):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        if not all(isinstance(e, ParamCollection) for e in self._asdict().values()):
            raise ValueError("inputs values be `ParamCollection`.")

    def decorate(self, name: str) -> Self:
        return self.__class__({k: v.decorate(name) for k, v in self._asdict().items()})


class InCollections(IOCollections[InCollection[Any]]):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        if not all(isinstance(v, InCollection) for v in self._asdict().values()):
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
                ((name, collection.get_required()) for name, collection in self._asdict().items()),
            )
        )


class OutCollections(IOCollections[OutCollection[Any]]):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        if not all(isinstance(v, OutCollection) for v in self._asdict().values()):
            raise ValueError("all `outputs` values need to be `Outputs` type.")

    def __rshift__(self, other: InCollections) -> IOCollectionDependencyOp:
        if not isinstance(other, InCollections):
            raise ValueError("Dependency assignment only accepts `InCollections`.")

        return IOCollectionDependencyOp(other, self)


class NoInCollections(InCollections):
    pass
    # def __getattr__(self, key: str) -> NoReturn:
    #     raise KeyError(f"InCollections has no attribute {key}.")


class NoOutCollections(OutCollections):
    pass
    # def __getattr__(self, key: str) -> NoReturn:
    #     raise KeyError(f"OutCollections has no attribute {key}.")


@dataclass
class PipelineConf:
    ...


TInputs = TypeVar("TInputs", bound=InCollection[Any])
TOutputs = TypeVar("TOutputs", bound=OutCollection[Any])
TInCollections = TypeVar("TInCollections", bound=InCollections)
TOutCollections = TypeVar("TOutCollections", bound=OutCollections)


class Pipeline(Generic[TInputs, TOutputs, TInCollections, TOutCollections]):
    _name: str
    _dag: DAG
    _config: PipelineConf
    _inputs: TInputs
    _outputs: TOutputs
    _in_collections: TInCollections
    _out_collections: TOutCollections

    @overload
    def __init__(
        self,
        *,
        other: Pipeline[TInputs, TOutputs, TInCollections, TOutCollections],
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
        inputs: TInputs,
        outputs: TOutputs,
        in_collections: TInCollections | None = None,
        out_collections: TOutCollections | None = None,
    ) -> None:
        ...

    def __init__(
        self,
        name: str | None = None,
        dag: DAG | None = None,
        config: PipelineConf | None = None,
        inputs: TInputs | None = None,
        outputs: TOutputs | None = None,
        in_collections: TInCollections | None = None,
        out_collections: TOutCollections | None = None,
        other: Pipeline[TInputs, TOutputs, TInCollections, TOutCollections] | None = None,
    ) -> None:
        if other is None:
            if not isinstance(name, str) or len(name) == 0:
                raise ValueError("Missing pipeline name.")
            if not isinstance(dag, DAG):
                raise ValueError(f"{dag} needs to be an instance of DAG.")
            if inputs is None:
                inputs = cast(TInputs, InCollection())
            if not isinstance(inputs, InCollection):
                raise ValueError("`inputs` need to be of `Inputs` type.")
            if outputs is None:
                outputs = cast(TOutputs, OutCollection())
            if not isinstance(outputs, OutCollection):
                raise ValueError("`outputs` needs to be of `Outputs` type.")
            if in_collections is None:
                in_collections = cast(TInCollections, InCollections())
            if not isinstance(in_collections, InCollections):
                raise ValueError("`in_collections` need to be of `InCollections` type.")
            if out_collections is None:
                out_collections = cast(TOutCollections, OutCollections())
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
        verify_pipeline_integrity(self)

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

    def __lshift__(self, other: UPipeline) -> PipelineDependencyOp:
        if not isinstance(other, Pipeline):
            raise ValueError("Dependency assignment only accepts another `TypedPipeline`.")

        return PipelineDependencyOp(cast(UPipeline, self), other)

    def __rshift__(self, other: UPipeline) -> PipelineDependencyOp:
        if not isinstance(other, Pipeline):
            raise ValueError("Dependency assignment only accepts `TypedPipeline`.")

        return PipelineDependencyOp(other, cast(UPipeline, self))

    def decorate(self, name: str) -> Pipeline[TInputs, TOutputs, TInCollections, TOutCollections]:
        dag = self._dag.decorate(name)
        inputs = self._inputs.decorate(name)
        outputs = self._outputs.decorate(name)
        in_collections = self._in_collections.decorate(name)
        out_collections = self._out_collections.decorate(name)
        return Pipeline(
            name=name,
            dag=dag,
            config=self._config,
            inputs=inputs,
            outputs=outputs,
            in_collections=in_collections,
            out_collections=out_collections,
        )

    @staticmethod
    def _fill_wildcard_collections(names: Mapping[str, str], io: PLi) -> Mapping[str, str]:
        resolved = dict[str, str]()

        def resolve_new_key(ok1: str, ok2: str, nk1: str, nk2: str) -> None:
            if nk1 == "*":
                nk1 = ok1
            if ok2:
                ok = f"{ok1}.{ok2}"
            else:
                ok = ok1
            if nk2:
                nk = f"{nk1}.{nk2}"
            else:
                nk = nk1
            resolved[ok] = nk

        for ok, nk in names.items():
            ok_split, nk_split = ok.split(".", 1), nk.split(".", 1)
            ok1, ok2 = ok_split if len(ok_split) == 2 else (ok, "")
            nk1, nk2 = nk_split if len(nk_split) == 2 else (nk, "")
            if not ok2:
                resolved[ok] = nk
            else:
                if ok1 != "*":
                    resolve_new_key(ok1, ok2, nk1, nk2)
                else:
                    for k1 in io:
                        if ok2 in io[k1]:
                            resolve_new_key(k1, ok2, nk1, nk2)
        return resolved

    @classmethod
    def _rename(cls, names: Mapping[str, str], collection: PCi, io: PLi) -> tuple[PCi, PLi]:
        if any(k.count(".") > 1 for k in chain.from_iterable(names.items())):
            raise ValueError("Names cannot contain more than single dot in keys or values.")

        names = cls._fill_wildcard_collections(names, io)

        for ok, nk in names.items():  # old key, new key
            ok_split, nk_split = ok.split(".", 1), nk.split(".", 1)
            ok1, ok2 = ok_split if len(ok_split) == 2 else (ok, "")
            nk1, nk2 = nk_split if len(nk_split) == 2 else (nk, "")
            if ok1 in io and ((ok2 and nk2) or not (ok2 or nk2)):
                # ParamCollection.ParamEntry -> ParamCollection.ParamEntry
                io = io._rename({ok: nk})  # or ParamCollection -> ParamCollection
            elif ok1 in collection and not ok2 and not nk2:  # ParamEntry -> ParamEntry
                collection = collection._rename({ok1: nk1})
            elif ok1 in collection and not ok2 and nk2:  # ParamEntry -> ParamCollection.ParamEntry
                io |= {nk1: getattr(io, nk1, collection.__class__()) | {nk2: collection[ok1]}}
                collection -= (ok1,)
            elif ok1 in io and ok2 and not nk2:  # ParamCollection.ParamEntry -> ParamEntry
                collection |= {nk: io[ok1][ok2]}
                io -= (f"{ok1}.{ok2}",)
            else:
                raise ValueError(f"Cannot rename {ok} to {nk}; non existing {ok} or wrong format.")

        return collection, io

    def rename_inputs(
        self, names: Mapping[str, str]
    ) -> Pipeline[Inputs, TOutputs, InCollections, TOutCollections]:
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

    def rename_outputs(
        self, names: Mapping[str, str]
    ) -> Pipeline[TInputs, Outputs, TInCollections, OutCollections]:
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
    def inputs(self) -> TInputs:
        return self._inputs

    @property
    def outputs(self) -> TOutputs:
        return self._outputs

    @property
    def in_collections(self) -> TInCollections:
        return self._in_collections

    @property
    def out_collections(self) -> TOutCollections:
        return self._out_collections

    @property
    def required_inputs(self) -> Inputs:
        return self._inputs.get_required()

    @property
    def required_in_collections(self) -> InCollections:
        return self._in_collections.get_required()


UPipeline = Pipeline[Inputs, Outputs, InCollections, OutCollections]
AnyPipeline = Pipeline[Any, Any, Any, Any]
