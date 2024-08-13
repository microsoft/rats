"""Run the docs commands."""

from rats import apps
from rats import docs as docs

app = apps.SimpleApplication("rats.devtools.plugins")
app.execute(docs.PluginServices.MAIN_EXE)
