from typing import Generic, TypeVar

from typing_extensions import NamedTuple

from ._executables import Executable

T_ServiceType = TypeVar("T_ServiceType")
T_ExecutableType = TypeVar("T_ExecutableType", bound=Executable)
Tco_ServiceType = TypeVar("Tco_ServiceType", covariant=True)


class ServiceId(NamedTuple, Generic[T_ServiceType]):
    name: str
