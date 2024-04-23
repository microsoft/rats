from typing import Protocol, TypeVar

T_ConfigType = TypeVar("T_ConfigType")


class IConfigService(Protocol):
    def __call__(self, config_type: type[T_ConfigType]) -> T_ConfigType: ...
