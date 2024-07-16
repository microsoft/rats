from typing import Generic, TypeVar
from typing import NamedTuple as tNamedTuple

from typing_extensions import NamedTuple

T_ServiceType = TypeVar("T_ServiceType")
T_ConfigType = TypeVar("T_ConfigType", bound=tNamedTuple)
Tco_ServiceType = TypeVar("Tco_ServiceType", covariant=True)
Tco_ConfigType = TypeVar("Tco_ConfigType", bound=tNamedTuple, covariant=True)


class ServiceId(NamedTuple, Generic[T_ServiceType]):
    name: str


class ConfigId(ServiceId[T_ConfigType]):
    pass
