from rats import apps


class Application(apps.AppContainer, apps.PluginMixin):

    def execute(self) -> None:
        print("hello, world!")
