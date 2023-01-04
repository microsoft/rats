from abc import abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Generic, Protocol, TypeVar

SettingType = TypeVar("SettingType")


@dataclass(frozen=True)
class SettingName(Generic[SettingType]):
    key: str


class IProvidePipelineSettings(Protocol):
    @abstractmethod
    def get(self, name: SettingName[SettingType]) -> SettingType:
        pass


class ISetPipelineSettings(Protocol):
    @abstractmethod
    def set(self, name: SettingName[SettingType], value: SettingType) -> None:
        pass


class IManagePipelineSettings(IProvidePipelineSettings, ISetPipelineSettings, Protocol):
    pass


class PipelineSettingsClient(IManagePipelineSettings):

    _settings: Dict[SettingName[Any], Any]

    def __init__(self) -> None:
        self._settings = {}

    def get(self, name: SettingName[SettingType]) -> SettingType:
        if name not in self._settings:
            raise PipelineSettingNotFoundError(name)

        return self._settings[name]

    def set(self, name: SettingName[SettingType], value: SettingType) -> None:
        # TODO: split up this class and limit things
        #     - should not be able to overwrite settings
        #     - should be able to layer cli settings after initialization
        self._settings[name] = value


class PipelineSettingNotFoundError(Exception):

    setting: SettingName[Any]

    def __init__(self, setting: SettingName[Any]) -> None:
        self.setting = setting
        super().__init__(f"Pipeline Setting Not Found: {self.setting.key}")
