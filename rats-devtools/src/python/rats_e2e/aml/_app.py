from rats import aml, apps


class Application(apps.AppContainer, apps.PluginMixin):

    def execute(self) -> None:
        print("hello, world!")
        for ctx in self._app.get_group(aml.AppConfigs.APP_CONTEXT):
            print(f"loaded context: {ctx}")
