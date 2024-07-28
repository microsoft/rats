"""Experimenting."""

from rats import apps
from rats import devtools as devtools

from ._plugin import PluginServices

app = apps.SimpleApplication("rats.apps.plugins", "rats.devtools.plugins", "rats.amlruntime")
tools = app.get(devtools.PluginServices.PROJECT_TOOLS)
tools.build_component_images()
app.get(PluginServices.AML_RUNTIME).execute(PluginServices.HELLO_WORLD)
