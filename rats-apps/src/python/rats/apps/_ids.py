from typing import Generic, ParamSpec, TypeVar

from typing_extensions import NamedTuple

P_ProviderParams = ParamSpec("P_ProviderParams")
T_ServiceType = TypeVar("T_ServiceType")
Tco_ServiceType = TypeVar("Tco_ServiceType", covariant=True)
T_ConfigType = TypeVar("T_ConfigType", bound=NamedTuple)
Tco_ConfigType = TypeVar("Tco_ConfigType", bound=NamedTuple, covariant=True)


class ServiceId(NamedTuple, Generic[T_ServiceType]):
    name: str


class ConfigId(ServiceId[T_ConfigType]):
    pass
