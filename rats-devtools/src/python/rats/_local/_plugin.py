from rats import apps

from ._amlruntimes import AmlRuntimePluginContainer
from ._kuberuntimes import KubeRuntimePluginContainer


class PluginContainer(apps.Container, apps.PluginMixin):

    @apps.container()
    def _plugins(self) -> apps.Container:
        return apps.CompositeContainer(
            AmlRuntimePluginContainer(self._app),
            KubeRuntimePluginContainer(self._app),
        )
