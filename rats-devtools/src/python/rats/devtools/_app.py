from rats import apps

from ._plugin import PluginServices


def run() -> None:
    app = apps.SimpleApplication(
        "rats.apps.plugins",
        "rats.devtools.plugins",
    )

    app.execute(PluginServices.MAIN)
