from abc import abstractmethod
from typing import Protocol

from ._session_client import PipelineSessionClient


class IPipelineSessionPlugin(Protocol):

    @abstractmethod
    def on_session_init(self, session_client: PipelineSessionClient) -> None:
        pass


class IRegisterPipelineSessionPlugins(Protocol):
    @abstractmethod
    def register_plugin(self, plugin: IPipelineSessionPlugin) -> None:
        pass


class IActivatePipelineSessionPlugins(Protocol):
    @abstractmethod
    def activate_all(self, session_client: PipelineSessionClient) -> None:
        pass


class IManagePipelineSessionPlugins(
        IRegisterPipelineSessionPlugins, IActivatePipelineSessionPlugins, Protocol):
    pass
