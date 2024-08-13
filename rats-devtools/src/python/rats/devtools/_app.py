from rats import apps

from ._plugin import PluginServices


def run(*plugin_groups: str) -> None:
    app = apps.SimpleApplication(
        "rats.apps.plugins",
        "rats.devtools.plugins",
        *plugin_groups,
    )

    app.execute_group(
        PluginServices.EVENTS.OPENING,
        PluginServices.EVENTS.RUNNING,
        PluginServices.EVENTS.CLOSING,
    )
