import logging
from enum import Enum, auto
from typing import Any, NamedTuple, cast

from oneml.pipelines.session import IExecutable
from oneml.pipelines.settings import IProvidePipelineSettings, SettingName

logger = logging.getLogger(__name__)


def _setting(name: str) -> SettingName[Any]:
    """Simple function to prepend the package to the setting so we avoid conflicts."""
    return SettingName(f"{__name__}.WorkflowPipelineSettings:{name}")


class NodeRole(Enum):
    DRIVER = auto()
    EXECUTOR = auto()


class _RemotePipelineSettings(NamedTuple):
    # I think we can create a decorator to auto-prefix all setting values
    NODE_ROLE: SettingName[NodeRole] = cast(SettingName[NodeRole], _setting("node-role"))
    DOCKER_IMAGE: SettingName[str] = cast(SettingName[str], _setting("docker-image"))


# This gets us a static set of constants for people to reference our settings
# WorkflowPipelineSettings.DOCKER_IMAGE
RemotePipelineSettings = _RemotePipelineSettings()


class RemoteContext:
    # TODO: RemoteContext is probably a bad name for this class
    _pipeline_settings: IProvidePipelineSettings

    def __init__(self, pipeline_settings: IProvidePipelineSettings) -> None:
        self._pipeline_settings = pipeline_settings

    def is_driver(self) -> bool:
        return self._pipeline_settings.get(RemotePipelineSettings.NODE_ROLE) == NodeRole.DRIVER


class RemoteExecutable(IExecutable):
    _context: RemoteContext
    _driver: IExecutable
    _executor: IExecutable

    def __init__(
        self,
        context: RemoteContext,
        driver: IExecutable,
        executor: IExecutable,
    ) -> None:
        self._context = context
        self._driver = driver
        self._executor = executor

    def execute(self) -> None:
        if self._context.is_driver():
            self._driver.execute()
        else:
            self._executor.execute()


class RemoteExecutableFactory:
    _context: RemoteContext
    _driver: IExecutable

    def __init__(
        self,
        context: RemoteContext,
        driver: IExecutable,
    ) -> None:
        self._context = context
        self._driver = driver

    def get_instance(self, executor: IExecutable) -> RemoteExecutable:
        return RemoteExecutable(
            context=self._context,
            driver=self._driver,
            executor=executor,
        )
