from rats import apps, logs

from ._plugin import PluginServices


def run(*plugin_groups: str) -> None:
    apps.run_plugin(logs.ConfigureApplication)
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
