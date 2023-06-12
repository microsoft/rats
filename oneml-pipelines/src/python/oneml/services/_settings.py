from abc import abstractmethod
from typing import Protocol

from ._setting_id import SettingId, SettingType


class SettingProvider(Protocol[SettingType]):
    """
    Callback that returns a single settings object.
    """

    @abstractmethod
    def __call__(self) -> SettingId[SettingType]:
        pass
