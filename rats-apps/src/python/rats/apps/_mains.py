import logging
from collections.abc import Callable

from ._app_containers import AppBundle, AppPlugin

logger = logging.getLogger(__name__)


def run_main(app_plugin: AppPlugin) -> None:
    """Shortcut to create and execute a script entry point."""
    make_main(app_plugin)()


def make_main(app_plugin: AppPlugin) -> Callable[[], None]:
    """
    Factory function to create an entry point for a python script.

    The `app_plugin` argument must be a callable that takes the root `apps.Container` and returns
    a new `apps.Container` instance that should be used as a child container for the application
    services.

    ```python
    from rats import apps

    from ._ids import PluginServices


    class ExampleAppContainer(rats.Container):
        _app: rats.Container

        def __init__(self, app: rats.Container) -> None:
            self._app = app

        @apps.service(PluginServices.Executables.MAIN)
        def _main(self) -> apps.Executable:
            return apps.App(lambda: print("hello, example app!"))


    def example_app() -> None:
        run_main(ExampleAppContainer)
    ```
    """

    def main() -> None:
        bundle = AppBundle(app_plugin=app_plugin)
        bundle.execute()

    return main
