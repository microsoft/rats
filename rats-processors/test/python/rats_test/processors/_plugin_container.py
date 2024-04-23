from rats import apps

from ._pipeline_container.example import ExampleContainer


class PluginContainer(apps.AnnotatedContainer):
    """rats.processors package top level container.

    Registered as into rats.processors_app_plugins in pyprotject.toml, and hence will be
    available in all apps that consume that plugin group.
    """

    def __init__(self, app: apps.Container) -> None:
        pass

    @apps.container()
    def example_container(self) -> ExampleContainer:
        return ExampleContainer()
