from abc import abstractmethod
from collections.abc import Iterable
from typing import Generic, Protocol, TypeVar

from typing_extensions import NamedTuple

T = TypeVar("T")
T_ServiceType = TypeVar("T_ServiceType")
Tco_ServiceType = TypeVar("Tco_ServiceType", covariant=True)


class ServiceId(NamedTuple, Generic[T_ServiceType]):
    name: str


class ServiceProvider(Protocol[Tco_ServiceType]):
    @abstractmethod
    def __call__(self) -> Tco_ServiceType: ...


class ServiceGroupProvider(Protocol[Tco_ServiceType]):
    @abstractmethod
    def __call__(self) -> Iterable[Tco_ServiceType]: ...
