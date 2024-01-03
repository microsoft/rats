from __future__ import annotations

import operator
from abc import abstractmethod, abstractproperty
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from functools import cached_property
from itertools import chain
from typing import (
    TYPE_CHECKING,
    Any,
    Generic,
    Protocol,
    SupportsIndex,
    final,
    overload,
)

from hydra_zen import hydrated_dataclass
from omegaconf import MISSING
from typing_extensions import Self, TypeVar

if TYPE_CHECKING:
    from ._pipeline import (
        InCollection,
        InCollections,
        InEntry,
        InParameter,
        OutCollection,
        OutCollections,
        OutEntry,
        OutParameter,
        UPipeline,
    )

T = TypeVar("T", bound=type | Any)


class _Decoratable(Protocol):
    @abstractmethod
    def decorate(self: Self, decoration: str) -> Self:
        ...


D = TypeVar("D", bound=_Decoratable)


def _maybe_decorate(target: D, decoration: str | None) -> D:
    decorated = target.decorate(decoration) if decoration else target
    return decorated


@final
@dataclass(frozen=True)
class Dependency(Generic[T]):
    in_param: InParameter[T]
    out_param: OutParameter[T]

    def __repr__(self) -> str:
        return f"{self.in_param!r} <- {self.out_param!r}"

    def decorate(self, in_name: str, out_name: str) -> Dependency[T]:
        return self.__class__(self.in_param.decorate(in_name), self.out_param.decorate(out_name))


class DependencyOp(Sequence[Dependency[T]]):
    @abstractproperty
    def dependencies(self) -> tuple[Dependency[T], ...]:
        ...

    @abstractmethod
    def decorate(self, in_name: str | None, out_name: str | None) -> DependencyOp[T]:
        ...

    @abstractmethod
    def get_dependencyopconf(self, pipelines: Sequence[UPipeline]) -> DependencyOpConf:
        ...

    def __add__(self, other: DependencyOp[T]) -> tuple[Dependency[T], ...]:
        return self.dependencies + tuple(other)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, DependencyOp) and self.dependencies == other.dependencies

    @overload
    def __getitem__(self, index: SupportsIndex) -> Dependency[T]:
        ...

    @overload
    def __getitem__(self, index: slice) -> tuple[Dependency[T], ...]:
        ...

    def __getitem__(
        self, index: SupportsIndex | slice
    ) -> Dependency[T] | tuple[Dependency[T], ...]:
        return self.dependencies[index]

    def __hash__(self) -> int:
        return hash(self.dependencies)

    def __iter__(self) -> Iterator[Dependency[T]]:
        return iter(self.dependencies)

    def __len__(self) -> int:
        return len(self.dependencies)

    def __repr__(self) -> str:
        return repr(self.dependencies)


@final
class EntryDependencyOp(DependencyOp[T]):
    in_entry: InEntry[T]
    out_entry: OutEntry[T]

    def __init__(self, in_entry: InEntry[T], out_entry: OutEntry[T]) -> None:
        self.in_entry = in_entry
        self.out_entry = out_entry

    @cached_property
    def dependencies(self) -> tuple[Dependency[T], ...]:
        return tuple(
            in_param << out_param for in_param in self.in_entry for out_param in self.out_entry
        )

    def decorate(self, in_name: str | None, out_name: str | None) -> DependencyOp[T]:
        in_entry = _maybe_decorate(self.in_entry, in_name)
        out_entry = _maybe_decorate(self.out_entry, out_name)
        return self.__class__(in_entry, out_entry)

    def get_dependencyopconf(self, pipelines: Sequence[UPipeline]) -> DependencyOpConf:
        inport_conf: PipelinePortConf | None = None
        outport_conf: PipelinePortConf | None = None
        for pl in pipelines:
            if inport_conf and outport_conf:
                break
            for k2, vii in pl.inputs._asdict().items():
                if vii == self.in_entry:
                    inport_conf = PipelinePortConf(pipeline=pl.name, port=f"inputs.{k2}")
                    continue
            for k2, voo in pl.outputs._asdict().items():
                if voo == self.out_entry:
                    outport_conf = PipelinePortConf(pipeline=pl.name, port=f"outputs.{k2}")
                    continue
            for k1, vi in pl.in_collections._asdict().items():
                for k2, vii in vi._asdict().items():
                    if vii == self.in_entry:
                        inport_conf = PipelinePortConf(pl.name, port=f"in_collections.{k1}.{k2}")
                        continue
            for k1, vo in pl.out_collections._asdict().items():
                for k2, voo in vo._asdict().items():
                    if voo == self.out_entry:
                        outport_conf = PipelinePortConf(pl.name, port=f"out_collections.{k1}.{k2}")
                        continue
        if inport_conf is None or outport_conf is None:
            raise ValueError("Dependencies do not come from any given pipeline.")

        return EntryDependencyOpConf(in_entry=inport_conf, out_entry=outport_conf)


@final
class CollectionDependencyOp(DependencyOp[T]):
    in_collection: InCollection[T]
    out_collection: OutCollection[T]

    def __init__(self, in_collection: InCollection[T], out_collection: OutCollection[T]) -> None:
        self.in_collection = in_collection
        self.out_collection = out_collection

    @cached_property
    def dependencies(self) -> tuple[Dependency[T], ...]:
        return tuple(
            dependency
            for in_assignname, in_entry in self.in_collection._asdict().items()
            for out_assignname, out_entry in self.out_collection._asdict().items()
            if in_assignname == out_assignname
            for dependency in out_entry >> in_entry
        )

    def decorate(self, in_name: str | None, out_name: str | None) -> DependencyOp[T]:
        in_collection = _maybe_decorate(self.in_collection, in_name)
        out_collection = _maybe_decorate(self.out_collection, out_name)
        return self.__class__(in_collection, out_collection)

    def get_dependencyopconf(self, pipelines: Sequence[UPipeline]) -> DependencyOpConf:
        inport_conf: PipelinePortConf | None = None
        outport_conf: PipelinePortConf | None = None
        for pl in pipelines:
            if inport_conf and outport_conf:
                break
            if pl.inputs == self.in_collection:
                inport_conf = PipelinePortConf(pipeline=pl.name, port="inputs")
                continue
            if pl.outputs == self.out_collection:
                outport_conf = PipelinePortConf(pipeline=pl.name, port="outputs")
                continue
            for k1, vi in pl.in_collections._asdict().items():
                if vi == self.in_collection:
                    inport_conf = PipelinePortConf(pipeline=pl.name, port=f"in_collections.{k1}")
                    continue
            for k1, vo in pl.out_collections._asdict().items():
                if vo == self.out_collection:
                    outport_conf = PipelinePortConf(pipeline=pl.name, port=f"out_collections.{k1}")
                    continue
        if inport_conf is None or outport_conf is None:
            raise ValueError("Dependencies do not come from any given pipeline.")

        return CollectionDependencyOpConf(in_collection=inport_conf, out_collection=outport_conf)


@final
class IOCollectionDependencyOp(DependencyOp[Any]):
    in_collections: InCollections
    out_collections: OutCollections

    def __init__(self, in_collections: InCollections, out_collections: OutCollections) -> None:
        self.in_collections = in_collections
        self.out_collections = out_collections

    @cached_property
    def dependencies(self) -> tuple[Dependency[Any], ...]:
        intersecting_keys = set(self.in_collections) & set(self.out_collections)
        dps = (tuple(self.in_collections[k] << self.out_collections[k]) for k in intersecting_keys)
        return tuple(chain.from_iterable(dps))

    def decorate(self, in_name: str | None, out_name: str | None) -> DependencyOp[Any]:
        in_collections = _maybe_decorate(self.in_collections, in_name)
        out_collections = _maybe_decorate(self.out_collections, out_name)
        return self.__class__(in_collections, out_collections)

    def get_dependencyopconf(self, pipelines: Sequence[UPipeline]) -> DependencyOpConf:
        inport_conf: PipelinePortConf | None = None
        outport_conf: PipelinePortConf | None = None
        for pl in pipelines:
            if inport_conf and outport_conf:
                break
            if pl.in_collections == self.in_collections:
                inport_conf = PipelinePortConf(pipeline=pl.name, port="in_collections")
                continue
            if pl.out_collections == self.out_collections:
                outport_conf = PipelinePortConf(pipeline=pl.name, port="out_collections")
                continue
        if inport_conf is None or outport_conf is None:
            raise ValueError("Dependencies do not come from any given pipeline.")

        return IOCollectionDependencyOpConf(
            in_collections=inport_conf, out_collections=outport_conf
        )


@final
class PipelineDependencyOp(DependencyOp[Any]):
    in_pipeline: UPipeline
    out_pipeline: UPipeline

    def __init__(
        self,
        in_pipeline: UPipeline,
        out_pipeline: UPipeline,
    ) -> None:
        self.in_pipeline = in_pipeline
        self.out_pipeline = out_pipeline

    @cached_property
    def dependencies(self) -> tuple[Dependency[Any], ...]:
        return tuple(self.in_pipeline.inputs << self.out_pipeline.outputs) + tuple(
            self.in_pipeline.in_collections << self.out_pipeline.out_collections
        )

    def decorate(self, in_name: str | None, out_name: str | None) -> DependencyOp[Any]:
        in_pipeline = _maybe_decorate(self.in_pipeline, in_name)
        out_pipeline = _maybe_decorate(self.out_pipeline, out_name)
        return self.__class__(in_pipeline, out_pipeline)

    def get_dependencyopconf(self, pipelines: Sequence[UPipeline]) -> DependencyOpConf:
        inport_conf: PipelinePortConf | None = None
        outport_conf: PipelinePortConf | None = None
        for pl in pipelines:
            if inport_conf and outport_conf:
                break
            if pl == self.in_pipeline:
                inport_conf = PipelinePortConf(pipeline=pl.name, port="")
                continue
            if pl == self.out_pipeline:
                outport_conf = PipelinePortConf(pipeline=pl.name, port="")
                continue
        if inport_conf is None or outport_conf is None:
            raise ValueError("Dependencies do not come from any given pipeline.")

        return PipelineDependencyOpConf(in_pipeline=inport_conf, out_pipeline=outport_conf)


def get_pipelineport(pipeline: UPipeline, port: str) -> Any:
    return operator.attrgetter(port)(pipeline) if len(port.split(".")) > 0 else pipeline


@hydrated_dataclass(get_pipelineport, zen_wrappers=["${parse_portpipeline:}"])
class PipelinePortConf:
    pipeline: Any = MISSING
    port: str = MISSING

    def rename_pipeline(self, name: str) -> PipelinePortConf:
        return self.__class__(name, self.port)


class DependencyOpConf:
    @abstractmethod
    def rename_pipelineports(self, in_name: str, out_name: str) -> DependencyOpConf:
        ...


@hydrated_dataclass(EntryDependencyOp)
class EntryDependencyOpConf(DependencyOpConf):
    in_entry: PipelinePortConf = MISSING
    out_entry: PipelinePortConf = MISSING

    def rename_pipelineports(self, in_name: str, out_name: str) -> DependencyOpConf:
        return self.__class__(
            self.in_entry.rename_pipeline(in_name), self.out_entry.rename_pipeline(out_name)
        )


@hydrated_dataclass(CollectionDependencyOp)
class CollectionDependencyOpConf(DependencyOpConf):
    in_collection: PipelinePortConf = MISSING
    out_collection: PipelinePortConf = MISSING

    def rename_pipelineports(self, in_name: str, out_name: str) -> DependencyOpConf:
        return self.__class__(
            self.in_collection.rename_pipeline(in_name),
            self.out_collection.rename_pipeline(out_name),
        )


@hydrated_dataclass(IOCollectionDependencyOp)
class IOCollectionDependencyOpConf(DependencyOpConf):
    in_collections: PipelinePortConf = MISSING
    out_collections: PipelinePortConf = MISSING

    def rename_pipelineports(self, in_name: str, out_name: str) -> DependencyOpConf:
        return self.__class__(
            self.in_collections.rename_pipeline(in_name),
            self.out_collections.rename_pipeline(out_name),
        )


@hydrated_dataclass(PipelineDependencyOp)
class PipelineDependencyOpConf(DependencyOpConf):
    in_pipeline: PipelinePortConf = MISSING
    out_pipeline: PipelinePortConf = MISSING

    def rename_pipelineports(self, in_name: str, out_name: str) -> DependencyOpConf:
        return self.__class__(
            self.in_pipeline.rename_pipeline(in_name), self.out_pipeline.rename_pipeline(out_name)
        )
