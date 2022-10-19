"""Processor providing know data as input to workflows."""

from typing import Any, Hashable, TypedDict

from ._environment_singletons import (
    EmptyParamsFromEnvironmentContract,
    IParamsFromEnvironmentSingletonsContract,
)
from ._pipeline import InSignature, OutParameter, OutSignature, PComputeReqs
from ._processor import IHashableGetParams, IProcess, KnownParamsGetter

# We can't hardcode the data type, and hence can't use standard ProcessorProps that infer output
# signature from `process` return type.
# Therefore we'll create a custom processor props class.

InputDataProviderProcessorOutputs = TypedDict("InputDataProviderProcessorOutputs", {"data": Any})


class InputDataProcessor(IProcess):
    def __init__(self, data: Any):
        self._data = data

    def process(self) -> InputDataProviderProcessorOutputs:
        return dict(data=self._data)


class InputDataProcessorProps:
    _data: Hashable

    def __init__(self, data: Hashable):
        self._data = data

    @property
    def processor_type(self) -> type[IProcess]:
        return InputDataProcessor

    @property
    def params_getter(self) -> IHashableGetParams:
        return KnownParamsGetter(dict(data=self._data))

    @property
    def params_from_environment_contract(self) -> IParamsFromEnvironmentSingletonsContract:
        return EmptyParamsFromEnvironmentContract()

    @property
    def compute_reqs(self) -> PComputeReqs:
        return PComputeReqs()

    @property
    def sig(self) -> InSignature:
        return InSignature()

    @property
    def ret(self) -> OutSignature:
        return OutSignature(data=OutParameter("data", type(self._data)))

    def __hash__(self) -> int:
        return hash(self._data)
