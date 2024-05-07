import logging

# pyright seems to struggle with this namespace package
# https://github.com/microsoft/pyright/issues/2882
from rats import apps as apps

from ._cli import DevtoolsCliPlugin
from ._cli_tree import DevtoolsCliTreePlugin
from ._ids import AppServices


class AppContainer(apps.AnnotatedContainer):
    @apps.container()
    def plugins(self) -> apps.Container:
        return apps.CompositeContainer(
            apps.PluginContainers(self, "rats.devtools.plugins"),
            DevtoolsCliPlugin(self),
            DevtoolsCliTreePlugin(self),
        )


def run() -> None:
    logging.basicConfig(level=logging.INFO)
    container = AppContainer()
    container.get(AppServices.CLI_EXE).execute()
