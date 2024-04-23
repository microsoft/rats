from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass
from typing import Any, Generic, NoReturn, cast, final, overload

from typing_extensions import Self, TypeVar

from ..dag import DAG, DagNode, InProcessorParam, OutProcessorParam
from ..utils import NamedCollection, SupportsAsDict, orderedset
from ._ops import CollectionDependencyOp, Dependency, EntryDependencyOp, PipelineDependencyOp
from ._verification import verify_pipeline_integrity

T = TypeVar("T", covariant=True)
PP = TypeVar("PP", bound=InProcessorParam | OutProcessorParam, covariant=True)
PM = TypeVar("PM", bound="PipelineParam[Any, Any]", covariant=True)
PE = TypeVar("PE", bound="ParamEntry[Any]", covariant=True)
PC = TypeVar("PC", bound="ParamCollection[Any]", covariant=True)


@dataclass(frozen=True, repr=False)
class PipelineParam(Generic[PP, T], ABC):
    node: DagNode
    param: PP

    def __post_init__(self) -> None:
        if not isinstance(self.node, DagNode):
            raise ValueError("`node` needs to be `DagNode`.")

    def __contains__(self, other: Any) -> bool:
        return other == self.param.name if isinstance(other, str) else other == self.param

    def __repr__(self) -> str:
        return self.__class__.__name__ + f"(node={self.node}, param={self.param.name})"

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
            raise ValueError("Not assigning outputs to inputs.")

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
            raise ValueError("Not assigning outputs to inputs.")

        return Dependency(other, self)


class ParamEntry(orderedset[PM], ABC):
    def __repr__(self) -> str:
        ann = str(self[0].param.annotation).replace("<class '", "").replace("'>", "")
        return f"{self.__class__.__name__}[{ann}]"

    def decorate(self, name: str) -> Self:
        return self.__class__(param.decorate(name) for param in self)


class InPort(ParamEntry[InParameter[T]]):
    def __init__(self, __iterable: Iterable[InParameter[T]] = ()) -> None:
        super().__init__(__iterable)
        if not all(isinstance(in_param, InParameter) for in_param in self):
            raise TypeError("All elements of `InPort` must be `InParameter`s.")

    @overload
    def __lshift__(self, other: OutPort[T]) -> EntryDependencyOp[T]: ...

    @overload
    def __lshift__(self, other: AnOutput) -> EntryDependencyOp[T]: ...

    def __lshift__(self, other: OutPort[T] | AnOutput) -> EntryDependencyOp[T]:
        if not isinstance(other, OutPort):
            raise TypeError("Cannot assign to `InPort`; `other` must be `OutPort`.")

        return EntryDependencyOp(self, other)

    @property
    def required(self) -> bool:
        return any(p.required for p in self)

    @property
    def optional(self) -> bool:
        return not self.required


class OutPort(ParamEntry[OutParameter[T]]):
    def __init__(self, __iterable: Iterable[OutParameter[T]] = ()) -> None:
        super().__init__(__iterable)
        if not all(isinstance(out_param, OutParameter) for out_param in self):
            raise TypeError("All elements of `OutPort` must be `OutParameter`s.")

    @overload
    def __rshift__(self, other: InPort[T]) -> EntryDependencyOp[T]: ...

    @overload
    def __rshift__(self, other: AnInput) -> EntryDependencyOp[T]: ...

    def __rshift__(self, other: InPort[T] | AnInput) -> EntryDependencyOp[T]:
        if not isinstance(other, InPort):
            raise TypeError("Cannot assign to `OutPort`; `other` must be `InPort`.")

        return EntryDependencyOp(other, self)


class ParamCollection(NamedCollection[PE], ABC):
    def decorate(self, name: str) -> Self:
        return self.__class__({k: entry.decorate(name) for k, entry in self._asdict().items()})


class InPorts(ParamCollection[InPort[T]]):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        if not all(isinstance(entry, InPort) for entry in self._asdict().values()):
            raise TypeError("Input values need to be `InPort` types.")

    @overload
    def __lshift__(self, other: OutPorts[T]) -> CollectionDependencyOp[T]: ...

    @overload
    def __lshift__(self, other: AnOutput) -> CollectionDependencyOp[T]: ...

    def __lshift__(self, other: OutPorts[T] | AnOutput) -> CollectionDependencyOp[T]:
        if not isinstance(other, OutPorts):
            raise TypeError("Cannot assign to `Inputs`; `other` must be `Outputs`.")

        return CollectionDependencyOp(self, other)

    def __getitem__(self, key: str) -> AnInput:
        return cast(AnInput, super().__getitem__(key))

    def __getattr__(self, key: str) -> AnInput:
        return cast(AnInput, super().__getattr__(key))

    def get_required(self) -> InPorts[T]:
        """Returns the subset of the inputs that are required."""
        return InPorts(filter(lambda t: t[1].required, self._asdict().items()))


class OutPorts(ParamCollection[OutPort[T]]):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        if not all(isinstance(entry, OutPort) for entry in self._asdict().values()):
            raise TypeError("Inputs values need to be `OutPort` types.")

    @overload
    def __rshift__(self, other: InPorts[T]) -> CollectionDependencyOp[T]: ...

    @overload
    def __rshift__(self, other: AnInput) -> CollectionDependencyOp[T]: ...

    def __rshift__(self, other: InPorts[T] | AnInput) -> CollectionDependencyOp[T]:
        if not isinstance(other, InPorts):
            raise TypeError("Cannot assign to `Outputs`; `other` must be `Inputs`.")

        return CollectionDependencyOp(other, self)

    def __getitem__(self, key: str) -> AnOutput:
        return cast(AnOutput, super().__getitem__(key))

    def __getattr__(self, key: str) -> AnOutput:
        return cast(AnOutput, super().__getattr__(key))


class AnInput(InPorts[Any], ABC):
    @abstractmethod
    def __iter__(self) -> Iterator[Any]: ...

    @overload
    @abstractmethod
    def __getitem__(self, key: str) -> AnInput: ...

    @overload
    @abstractmethod
    def __getitem__(self, key: int) -> InParameter[Any]: ...

    @abstractmethod
    def __getitem__(self, key: str | int) -> AnInput | InParameter[Any]: ...

    @abstractmethod
    def __getattr__(self, key: str) -> AnInput: ...

    @abstractmethod
    def __len__(self) -> int: ...

    @abstractmethod
    def __or__(
        self, other: SupportsAsDict[InPort[Any]] | Mapping[str, InPort[Any]]
    ) -> AnInput: ...

    @abstractmethod
    def __lshift__(
        self, other: AnOutput | OutPorts[Any] | OutPort[Any]
    ) -> CollectionDependencyOp[Any]: ...

    @abstractmethod
    def _asdict(self) -> dict[str, InPort[Any]]: ...

    @abstractmethod
    def decorate(self, name: str) -> AnInput: ...


class AnOutput(OutPorts[Any], ABC):
    @abstractmethod
    def __iter__(self) -> Iterator[Any]: ...

    @abstractmethod
    def __len__(self) -> int: ...

    @overload
    @abstractmethod
    def __getitem__(self, key: str) -> AnOutput: ...

    @overload
    @abstractmethod
    def __getitem__(self, key: int) -> OutParameter[Any]: ...

    @overload
    @abstractmethod
    def __getitem__(self, key: str | int) -> AnOutput | OutParameter[Any]: ...

    @abstractmethod
    def __getattr__(self, key: str) -> AnOutput: ...

    @abstractmethod
    def __or__(
        self, other: SupportsAsDict[OutPort[Any]] | Mapping[str, OutPort[Any]]
    ) -> AnOutput: ...

    @abstractmethod
    def __rshift__(
        self, other: AnInput | InPort[Any] | InPorts[Any]
    ) -> CollectionDependencyOp[Any]: ...

    @abstractmethod
    def _asdict(self) -> dict[str, OutPort[Any]]: ...

    @abstractmethod
    def decorate(self, name: str) -> AnOutput: ...


Inputs = InPorts[Any]
Outputs = OutPorts[Any]


class NoInputs(Inputs):
    def __getitem__(self, key: str) -> NoReturn:
        raise KeyError(f"Inputs has no attribute {key}.")

    def __getattr__(self, key: str) -> NoReturn:
        raise KeyError(f"Inputs has no attribute {key}.")


class NoOutputs(Outputs):
    def __getitem__(self, key: str) -> NoReturn:
        raise KeyError(f"Outputs has no attribute {key}.")

    def __getattr__(self, key: str) -> NoReturn:
        raise KeyError(f"Outputs has no attribute {key}.")


@dataclass
class PipelineConf: ...


TInputs = TypeVar("TInputs", bound=Inputs, covariant=True)
TOutputs = TypeVar("TOutputs", bound=Outputs, covariant=True)


class Pipeline(Generic[TInputs, TOutputs]):
    _name: str
    _dag: DAG
    _config: PipelineConf
    _inputs: TInputs
    _outputs: TOutputs

    @overload
    def __init__(
        self, *, other: Pipeline[TInputs, TOutputs], config: PipelineConf | None = None
    ) -> None: ...

    @overload
    def __init__(
        self, *, name: str, dag: DAG, config: PipelineConf, inputs: TInputs, outputs: TOutputs
    ) -> None: ...

    def __init__(
        self,
        name: str | None = None,
        dag: DAG | None = None,
        config: PipelineConf | None = None,
        inputs: TInputs | None = None,
        outputs: TOutputs | None = None,
        other: Pipeline[TInputs, TOutputs] | None = None,
    ) -> None:
        if other is None:
            if not isinstance(name, str) or len(name) == 0:
                raise ValueError("Missing pipeline name.")
            if not isinstance(dag, DAG):
                raise ValueError(f"{dag} needs to be an instance of DAG.")
            if inputs is None:
                inputs = cast(TInputs, InPorts())
            if not isinstance(inputs, InPorts):
                raise ValueError("`inputs` need to be of `Inputs` type.")
            if outputs is None:
                outputs = cast(TOutputs, OutPorts())
            if not isinstance(outputs, OutPorts):
                raise ValueError("`outputs` needs to be of `Outputs` type.")
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
            if len(spurious_params) > 1:
                raise ValueError(
                    "When `other` is given, the following params should not be given: "
                    + f"{spurious_params}."
                )
            name = other._name
            inputs = other._inputs
            outputs = other._outputs
            dag = other._dag
            if config is None:
                config = other._config

        self._name = name
        self._inputs = inputs
        self._outputs = outputs
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

    def decorate(self, name: str) -> Pipeline[TInputs, TOutputs]:
        dag = self._dag.decorate(name)
        inputs = self._inputs.decorate(name)
        outputs = self._outputs.decorate(name)
        return Pipeline(name=name, dag=dag, config=self._config, inputs=inputs, outputs=outputs)

    def rename_inputs(self, names: Mapping[str, str]) -> Pipeline[Inputs, TOutputs]:
        return Pipeline(
            name=self.name,
            dag=self._dag,
            config=self._config,
            inputs=self.inputs._rename(names),
            outputs=self.outputs,
        )

    def rename_outputs(self, names: Mapping[str, str]) -> Pipeline[TInputs, Outputs]:
        return Pipeline(
            name=self.name,
            dag=self._dag,
            config=self._config,
            inputs=self.inputs,
            outputs=self.outputs._rename(names),
        )

    def drop_inputs(self, *names: str) -> Pipeline[Inputs, TOutputs]:
        required = []
        for name in names:
            if self.inputs[name].required:
                required.append(name)
        if len(required) > 0:
            raise ValueError(f"Cannot drop required inputs: {required}.")

        return Pipeline(
            name=self.name,
            dag=self._dag,
            config=self._config,
            inputs=self.inputs - names,
            outputs=self.outputs,
        )

    def drop_outputs(self, *names: str) -> Pipeline[TInputs, Outputs]:
        return Pipeline(
            name=self.name,
            dag=self._dag,
            config=self._config,
            inputs=self.inputs,
            outputs=self.outputs - names,
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
    def required_inputs(self) -> Inputs:
        return self._inputs.get_required()


UPipeline = Pipeline[Inputs, Outputs]
