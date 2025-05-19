from collections.abc import Iterator

from rats import apps, runtime

from ._data import ExampleData


@apps.autoscope
class AppServices:
    EXAMPLE_DATA = apps.ServiceId[ExampleData]("example-data")


class Application(apps.AppContainer, apps.PluginMixin):
    def execute(self) -> None:
        print("hello, world!")
        print(f"looking for any registered context: {AppServices.EXAMPLE_DATA.name}")
        for data in self._app.get_group(AppServices.EXAMPLE_DATA):
            print(f"found example data element: {data}")

    @apps.fallback_group(AppServices.EXAMPLE_DATA)
    def _data_from_context(self) -> Iterator[ExampleData]:
        collection = self._app.get(runtime.AppServices.CONTEXT)
        yield from collection.decoded_values(ExampleData, AppServices.EXAMPLE_DATA)
