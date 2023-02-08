import logging
from enum import Enum, auto
from typing import Any, NamedTuple, cast

from oneml.pipelines.building._executable_pickling import (
    ExecutablePicklingClient,
    PickleableExecutable,
)
from oneml.pipelines.context._client import IProvideExecutionContexts
from oneml.pipelines.session import IExecutable, PipelineSessionClient
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
    FORCE_LOCAL: SettingName[bool] = cast(SettingName[bool], _setting("force-local"))


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

    def is_force_local(self) -> bool:
        return self._pipeline_settings.get(RemotePipelineSettings.FORCE_LOCAL)


class RemoteExecutable(IExecutable):
    _context: RemoteContext
    _session_context: IProvideExecutionContexts[PipelineSessionClient]
    # TODO: find a better name for _driver
    _driver: IExecutable
    _executor: PickleableExecutable
    _pickler: ExecutablePicklingClient

    def __init__(
        self,
        context: RemoteContext,
        session_context: IProvideExecutionContexts[PipelineSessionClient],
        driver: IExecutable,
        executor: PickleableExecutable,
        pickler: ExecutablePicklingClient,
    ) -> None:
        self._context = context
        self._session_context = session_context
        self._driver = driver
        self._executor = executor
        self._pickler = pickler

    def execute(self) -> None:
        # TODO: When we use Argo, we would never need to execute the executable on the driver.
        #       We should move this so all the pickling happens at session build time.
        #       We could standardize to always have a driver, which during local execution,
        #       would just execute the executable.
        if self._context.is_driver():
            # The executor here is the original executable
            self._pickler.save_active_node(self._executor)
            if self._context.is_force_local():
                self._executor.execute(self._session_context.get_context())
            else:
                self._driver.execute()
        else:
            self._executor.execute(self._session_context.get_context())


class RemoteExecutableFactory:
    _context: RemoteContext
    _session_context: IProvideExecutionContexts[PipelineSessionClient]
    _driver: IExecutable
    _pickler: ExecutablePicklingClient

    def __init__(
        self,
        context: RemoteContext,
        session_context: IProvideExecutionContexts[PipelineSessionClient],
        driver: IExecutable,
        pickler: ExecutablePicklingClient,
    ) -> None:
        self._context = context
        self._session_context = session_context
        self._driver = driver
        self._pickler = pickler

    def get_instance(self, executor: PickleableExecutable) -> RemoteExecutable:
        return RemoteExecutable(
            context=self._context,
            session_context=self._session_context,
            driver=self._driver,
            executor=executor,
            pickler=self._pickler,
        )