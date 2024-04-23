from rats import apps

from ._legacy_services_wrapper import LegacyServicesWrapperContainer


class PluginContainer(apps.AnnotatedContainer):
    """rats.processors package top level container.

    Registered as into rats.processors_app_plugins in pyprotject.toml, and hence will be
    available in all apps that consume that plugin group.
    """

    def __init__(self, app: apps.Container) -> None:
        pass

    @apps.container()
    def legacy_services(self) -> LegacyServicesWrapperContainer:
        return LegacyServicesWrapperContainer()
