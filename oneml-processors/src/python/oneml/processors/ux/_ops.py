from __future__ import annotations

import operator
from abc import abstractmethod, abstractproperty
from dataclasses import dataclass
from functools import cached_property
from itertools import chain
from typing import TYPE_CHECKING, Any, Iterator, Sequence, SupportsIndex, final, overload

from hydra_zen import hydrated_dataclass
from omegaconf import MISSING

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
        Pipeline,
    )


@final
@dataclass(frozen=True)
class Dependency:
    in_param: InParameter
    out_param: OutParameter

    def __repr__(self) -> str:
        return f"{repr(self.in_param)} <- {repr(self.out_param)}"

    def decorate(self, in_name: str, out_name: str) -> Dependency:
        return self.__class__(self.in_param.decorate(in_name), self.out_param.decorate(out_name))


class DependencyOp(Sequence[Dependency]):
    @abstractproperty
    def dependencies(self) -> tuple[Dependency, ...]:
        ...

    @abstractmethod
    def decorate(self, in_name: str, out_name: str) -> DependencyOp:
        ...

    @abstractmethod
    def get_dependencyopconf(self, pipelines: Sequence[Pipeline]) -> DependencyOpConf:
        ...

    def __add__(self, other: DependencyOp) -> tuple[Dependency, ...]:
        return self.dependencies + tuple(other)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, DependencyOp) and self.dependencies == other.dependencies

    @overload
    def __getitem__(self, index: SupportsIndex) -> Dependency:
        ...

    @overload
    def __getitem__(self, index: slice) -> tuple[Dependency, ...]:
        ...

    def __getitem__(self, index: SupportsIndex | slice) -> Dependency | tuple[Dependency, ...]:
        return self.dependencies[index]

    def __hash__(self) -> int:
        return hash(self.dependencies)

    def __iter__(self) -> Iterator[Dependency]:
        return iter(self.dependencies)

    def __len__(self) -> int:
        return len(self.dependencies)

    def __repr__(self) -> str:
        return repr(self.dependencies)


@final
class EntryDependencyOp(DependencyOp):
    in_entry: InEntry
    out_entry: OutEntry

    def __init__(self, in_entry: InEntry, out_entry: OutEntry) -> None:
        self.in_entry = in_entry
        self.out_entry = out_entry

    @cached_property
    def dependencies(self) -> tuple[Dependency, ...]:
        return tuple(
            in_param << out_param for in_param in self.in_entry for out_param in self.out_entry
        )

    def decorate(self, in_name: str, out_name: str) -> DependencyOp:
        return self.__class__(self.in_entry.decorate(in_name), self.out_entry.decorate(out_name))

    def get_dependencyopconf(self, pipelines: Sequence[Pipeline]) -> DependencyOpConf:
        inport_conf: PipelinePortConf | None = None
        outport_conf: PipelinePortConf | None = None
        for pl in pipelines:
            if inport_conf and outport_conf:
                break
            for k2, vii in pl.inputs.items():
                if vii == self.in_entry:
                    inport_conf = PipelinePortConf(pipeline=pl.name, port=f"inputs.{k2}")
                    continue
            for k2, voo in pl.outputs.items():
                if voo == self.out_entry:
                    outport_conf = PipelinePortConf(pipeline=pl.name, port=f"outputs.{k2}")
                    continue
            for k1, vi in pl.in_collections.items():
                for k2, vii in vi.items():
                    if vii == self.in_entry:
                        inport_conf = PipelinePortConf(pl.name, port=f"in_collections.{k1}.{k2}")
                        continue
            for k1, vo in pl.out_collections.items():
                for k2, voo in vo.items():
                    if voo == self.out_entry:
                        outport_conf = PipelinePortConf(pl.name, port=f"out_collections.{k1}.{k2}")
                        continue
        if inport_conf is None or outport_conf is None:
            raise ValueError("Dependencies do not come from any given pipeline.")

        return EntryDependencyOpConf(in_entry=inport_conf, out_entry=outport_conf)


@final
class CollectionDependencyOp(DependencyOp):
    in_collection: InCollection
    out_collection: OutCollection

    def __init__(self, in_collection: InCollection, out_collection: OutCollection) -> None:
        self.in_collection = in_collection
        self.out_collection = out_collection

    @cached_property
    def dependencies(self) -> tuple[Dependency, ...]:
        return tuple(
            dependency
            for in_assignname, in_entry in self.in_collection.items()
            for out_assignname, out_entry in self.out_collection.items()
            if in_assignname == out_assignname
            for dependency in out_entry >> in_entry
        )

    def decorate(self, in_name: str, out_name: str) -> DependencyOp:
        return self.__class__(
            self.in_collection.decorate(in_name), self.out_collection.decorate(out_name)
        )

    def get_dependencyopconf(self, pipelines: Sequence[Pipeline]) -> DependencyOpConf:
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
            for k1, vi in pl.in_collections.items():
                if vi == self.in_collection:
                    inport_conf = PipelinePortConf(pipeline=pl.name, port=f"in_collections.{k1}")
                    continue
            for k1, vo in pl.out_collections.items():
                if vo == self.out_collection:
                    outport_conf = PipelinePortConf(pipeline=pl.name, port=f"out_collections.{k1}")
                    continue
        if inport_conf is None or outport_conf is None:
            raise ValueError("Dependencies do not come from any given pipeline.")

        return CollectionDependencyOpConf(in_collection=inport_conf, out_collection=outport_conf)


@final
class IOCollectionDependencyOp(DependencyOp):
    in_collections: InCollections
    out_collections: OutCollections

    def __init__(self, in_collections: InCollections, out_collections: OutCollections) -> None:
        self.in_collections = in_collections
        self.out_collections = out_collections

    @cached_property
    def dependencies(self) -> tuple[Dependency, ...]:
        intersecting_keys = set(self.in_collections) & set(self.out_collections)
        dps = (tuple(self.in_collections[k] << self.out_collections[k]) for k in intersecting_keys)
        return tuple(chain.from_iterable(dps))

    def decorate(self, in_name: str, out_name: str) -> DependencyOp:
        return self.__class__(
            self.in_collections.decorate(in_name), self.out_collections.decorate(out_name)
        )

    def get_dependencyopconf(self, pipelines: Sequence[Pipeline]) -> DependencyOpConf:
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
class PipelineDependencyOp(DependencyOp):
    in_pipeline: Pipeline
    out_pipeline: Pipeline

    def __init__(self, in_pipeline: Pipeline, out_pipeline: Pipeline) -> None:
        self.in_pipeline = in_pipeline
        self.out_pipeline = out_pipeline

    @cached_property
    def dependencies(self) -> tuple[Dependency, ...]:
        return tuple(self.in_pipeline.inputs << self.out_pipeline.outputs) + tuple(
            self.in_pipeline.in_collections << self.out_pipeline.out_collections
        )

    def decorate(self, in_name: str, out_name: str) -> DependencyOp:
        return self.__class__(
            self.in_pipeline.decorate(in_name), self.out_pipeline.decorate(out_name)
        )

    def get_dependencyopconf(self, pipelines: Sequence[Pipeline]) -> DependencyOpConf:
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


def get_pipelineport(pipeline: Pipeline, port: str) -> Any:
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
