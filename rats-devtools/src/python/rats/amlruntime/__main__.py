from rats import apps

from ._plugin import PluginServices

app = apps.SimpleApplication("rats.apps.plugins", "rats.amlruntime")
app.get(PluginServices.AML_RUNTIME).execute(PluginServices.HELLO_WORLD)
