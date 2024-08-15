from rats import apps

from ._amlruntimes import AmlRuntimePluginContainer
from ._examples import ExamplesPluginContainer
from ._kuberuntimes import KubeRuntimePluginContainer


class PluginContainer(apps.Container):
    _app: apps.Container

    def __init__(self, app: apps.Container) -> None:
        self._app = app

    @apps.container()
    def _plugins(self) -> apps.Container:
        return apps.CompositeContainer(
            AmlRuntimePluginContainer(self._app),
            KubeRuntimePluginContainer(self._app),
            ExamplesPluginContainer(self._app),
        )
