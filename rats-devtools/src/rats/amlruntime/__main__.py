"""Run the amlruntime commands."""

from rats import amlruntime as amlruntime
from rats import apps
from rats import devtools as devtools

app = apps.AppBundle(app_plugin=devtools.Application)
app.get(amlruntime.PluginServices.MAIN_CLICK)()
