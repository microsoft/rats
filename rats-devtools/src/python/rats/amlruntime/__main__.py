"""Run the amlruntime commands."""

from rats import amlruntime as amlruntime
from rats import apps

app = apps.SimpleApplication("rats.devtools.plugins")
app.execute(amlruntime.PluginServices.MAIN_EXE)
