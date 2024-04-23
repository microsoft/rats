from rats import apps


class PluginContainer(apps.AnnotatedContainer):
    """rats_test.processors package top level container.

    Registered as into rats.processors_app_plugins in pyprotject.toml, and hence will be
    available in all apps that consume that plugin group.
    """

    def __init__(self, app: apps.Container) -> None:
        pass
