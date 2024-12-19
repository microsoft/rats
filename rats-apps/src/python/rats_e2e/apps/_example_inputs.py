from rats import apps

from ._services import ExampleAppServices


class InputExampleApp(apps.AppContainer, apps.PluginMixin):
    def execute(self) -> None:
        print(f"running ExampleApp instance: {self}")
        print(f"example app executed with input: {self._app.get(ExampleAppServices.INPUT)}")

    @apps.fallback_service(ExampleAppServices.INPUT)
    def _default_input(self) -> str:
        # we can throw an exception if we want the input to be required without defaults
        return "NO INPUT SPECIFIED"
