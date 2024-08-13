"""Run the ci commands."""

from rats import apps
from rats import ci as ci

app = apps.SimpleApplication("rats.devtools.plugins")
app.execute(ci.PluginServices.MAIN_EXE)
