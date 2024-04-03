from __future__ import annotations

import operator
from abc import abstractmethod
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from functools import cached_property
from typing import TYPE_CHECKING, Any, Generic, Protocol, SupportsIndex, final, overload

from hydra_zen import hydrated_dataclass
from omegaconf import MISSING
from typing_extensions import Self, TypeVar

from ..utils import namedcollection

if TYPE_CHECKING:
    from ._pipeline import InParameter, InPort, InPorts, OutParameter, OutPort, OutPorts, UPipeline

T = TypeVar("T", bound=type | Any)


class _Decoratable(Protocol):
    @abstractmethod
    def decorate(self, name: str) -> Self: ...


D = TypeVar("D", bound=_Decoratable)


def _maybe_decorate(target: D, decoration: str | None) -> D:
    return target.decorate(decoration) if decoration else target


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
    @property
    @abstractmethod
    def dependencies(self) -> tuple[Dependency[T], ...]: ...

    @abstractmethod
    def decorate(self, in_name: str | None, out_name: str | None) -> DependencyOp[T]: ...

    @abstractmethod
    def get_dependencyopconf(self, pipelines: Sequence[UPipeline]) -> DependencyOpConf: ...

    def __add__(self, other: DependencyOp[T]) -> tuple[Dependency[T], ...]:
        return self.dependencies + tuple(other)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, DependencyOp) and self.dependencies == other.dependencies

    @overload
    def __getitem__(self, index: SupportsIndex) -> Dependency[T]: ...

    @overload
    def __getitem__(self, index: slice) -> tuple[Dependency[T], ...]: ...

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
    in_entry: InPort[T]
    out_entry: OutPort[T]

    def __init__(self, in_entry: InPort[T], out_entry: OutPort[T]) -> None:
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
            # TODO: need to search recursively through in_collections and out_collections

        if inport_conf is None or outport_conf is None:
            raise ValueError("Dependencies do not come from any given pipeline.")

        return EntryDependencyOpConf(in_entry=inport_conf, out_entry=outport_conf)


@final
class CollectionDependencyOp(DependencyOp[T]):
    in_collection: InPorts[T]
    out_collection: OutPorts[T]

    def __init__(self, in_collection: InPorts[T], out_collection: OutPorts[T]) -> None:
        xor = set(in_collection) ^ set(out_collection)
        assert (in_collection - xor)._depth == (out_collection - xor)._depth
        self.in_collection = in_collection
        self.out_collection = out_collection
        _ = self.dependencies

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

        def rsearch(nc: Any, target: Any, port: str) -> PipelinePortConf | None:
            if set(nc._asdict().values()) >= set(target._asdict().values()):
                return PipelinePortConf(pipeline=pl.name, port=port)
            else:
                for k in nc:
                    if isinstance(nc[k], namedcollection):
                        return rsearch(nc[k], target, f"{port}.{k}")
            return None

        for pl in pipelines:
            if inport_conf and outport_conf:
                break
            if inport_conf is None:
                inport_conf = rsearch(pl.inputs, self.in_collection, "inputs")
            if outport_conf is None:
                outport_conf = rsearch(pl.outputs, self.out_collection, "outputs")

        if inport_conf is None or outport_conf is None:
            raise ValueError("Dependencies do not come from any given pipeline.")

        return CollectionDependencyOpConf(in_collection=inport_conf, out_collection=outport_conf)


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
        return tuple(self.in_pipeline.inputs << self.out_pipeline.outputs)

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
    def rename_pipelineports(self, in_name: str, out_name: str) -> DependencyOpConf: ...


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


@hydrated_dataclass(PipelineDependencyOp)
class PipelineDependencyOpConf(DependencyOpConf):
    in_pipeline: PipelinePortConf = MISSING
    out_pipeline: PipelinePortConf = MISSING

    def rename_pipelineports(self, in_name: str, out_name: str) -> DependencyOpConf:
        return self.__class__(
            self.in_pipeline.rename_pipeline(in_name), self.out_pipeline.rename_pipeline(out_name)
        )
