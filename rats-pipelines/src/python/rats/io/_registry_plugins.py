import logging

from rats.services import IExecutable, ServiceGroupProvider

logger = logging.getLogger(__name__)


class IoRegistryPluginsExe(IExecutable):
    _group: ServiceGroupProvider[IExecutable]

    def __init__(self, group: ServiceGroupProvider[IExecutable]) -> None:
        self._group = group

    def execute(self) -> None:
        logger.debug("initializing io plugins")
        for plugin in self._group():
            plugin.execute()
