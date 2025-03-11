import logging

from ._app_containers import AppBundle, AppPlugin
from ._executables import Executable

logger = logging.getLogger(__name__)


def run(*apps: Executable) -> None:
    """Shortcut for running a list of apps."""
    for app in apps:
        app.execute()


def run_plugin(*app_plugins: AppPlugin) -> None:
    """
    Shortcut to create and execute instances of `apps.AppPlugin`.

    This function is most commonly used in a `console_script` function `main()` entry point.

    Example:
        ```python
        from rats import apps


        class Application(apps.AppContainer, apps.AppPlugin):
            def execute(self) -> None:
                print("hello, world")


        def main() -> None:
            apps.run_plugin(Application)


        if __name__ == "__main__":
            main()
        ```

    Args:
        *app_plugins: one or more class types to be instantiated and executed.
    """
    run(*[AppBundle(app_plugin=plugin) for plugin in app_plugins])
