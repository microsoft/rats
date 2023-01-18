from abc import abstractmethod
from typing import Any, Dict, Protocol

from oneml.pipelines.dag import PipelineNode

from ._entities import SettingName, SettingType


class IProvideNodeSettings(Protocol):
    @abstractmethod
    def get(self, node: PipelineNode, name: SettingName[SettingType]) -> SettingType:
        """"""


class ISetNodeSettings(Protocol):
    @abstractmethod
    def set(self, node: PipelineNode, name: SettingName[SettingType], value: SettingType) -> None:
        """"""


class IManageNodeSettings(IProvideNodeSettings, ISetNodeSettings, Protocol):
    """"""


class NodeSettingsClient(IManageNodeSettings):

    _settings: Dict[PipelineNode, Dict[SettingName[Any], Any]]

    def __init__(self) -> None:
        self._settings = {}

    def get(self, node: PipelineNode, name: SettingName[SettingType]) -> SettingType:
        node_settings = self._settings.get(node, {})
        if name not in node_settings:
            raise NodeSettingNotFoundError(node, name)

        return node_settings[name]

    def set(self, node: PipelineNode, name: SettingName[SettingType], value: SettingType) -> None:
        if node not in self._settings:
            self._settings[node] = {}

        if name in self._settings[node]:
            raise DuplicateNodeSettingError(node, name)

        self._settings[node][name] = value


class NodeSettingNotFoundError(Exception):

    node: PipelineNode
    setting: SettingName[Any]

    def __init__(self, node: PipelineNode, setting: SettingName[Any]) -> None:
        self.node = node
        self.setting = setting
        super().__init__(f"Node Setting Not Found: {setting.key}[{node.key}]")


class DuplicateNodeSettingError(Exception):

    node: PipelineNode
    setting: SettingName[Any]

    def __init__(self, node: PipelineNode, setting: SettingName[Any]) -> None:
        self.node = node
        self.setting = setting
        super().__init__(f"Duplicate Node Setting Found: {setting.key}[{node.key}]")
