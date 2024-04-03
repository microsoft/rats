from typing import Generic, ParamSpec, TypeVar

from typing_extensions import NamedTuple

P_ProviderParams = ParamSpec("P_ProviderParams")
T_ServiceType = TypeVar("T_ServiceType")
T_ConfigType = TypeVar("T_ConfigType", bound=NamedTuple)


class ServiceId(NamedTuple, Generic[T_ServiceType]):
    name: str


class ConfigId(ServiceId[T_ConfigType]):
    pass
