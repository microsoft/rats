from abc import abstractmethod
from typing import Any, Dict, Protocol

from ._entities import SettingName, SettingType


class IProvidePipelineSettings(Protocol):
    @abstractmethod
    def get(self, name: SettingName[SettingType]) -> SettingType:
        """"""


class ISetPipelineSettings(Protocol):
    @abstractmethod
    def set(self, name: SettingName[SettingType], value: SettingType) -> None:
        """"""


class IManagePipelineSettings(IProvidePipelineSettings, ISetPipelineSettings, Protocol):
    """"""


class PipelineSettingsClient(IManagePipelineSettings):

    _settings: Dict[SettingName[Any], Any]

    def __init__(self) -> None:
        self._settings = {}

    def get(self, name: SettingName[SettingType]) -> SettingType:
        if name not in self._settings:
            raise PipelineSettingNotFoundError(name)

        return self._settings[name]

    def set(self, name: SettingName[SettingType], value: SettingType) -> None:
        if name in self._settings:
            raise DuplicatePipelineSettingError(name)

        self._settings[name] = value


class PipelineSettingNotFoundError(Exception):

    setting: SettingName[Any]

    def __init__(self, setting: SettingName[Any]) -> None:
        self.setting = setting
        super().__init__(f"Pipeline Setting Not Found: {self.setting.key}")


class DuplicatePipelineSettingError(Exception):

    setting: SettingName[Any]

    def __init__(self, setting: SettingName[Any]) -> None:
        self.setting = setting
        super().__init__(f"Duplicate Pipeline Setting Found: {self.setting.key}")
