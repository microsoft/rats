from dataclasses import dataclass
from typing import Generic, TypeVar

SettingType = TypeVar("SettingType")


@dataclass(frozen=True)
class SettingName(Generic[SettingType]):
    key: str
