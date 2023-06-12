from typing import Generic, TypeVar

from typing_extensions import NamedTuple

SettingType = TypeVar("SettingType", bound=NamedTuple)


class SettingId(NamedTuple, Generic[SettingType]):
    name: str
