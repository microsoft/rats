from rats import apps

from ._plugin import PluginServices


def run() -> None:
    app = apps.SimpleApplication(
        "rats.apps.plugins",
        "rats.devtools.plugins",
    )

    def _main() -> None:
        app.execute(PluginServices.MAIN)

    app.execute_callable(_main)
