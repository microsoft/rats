"""Run the ci commands."""

from rats import apps as apps
from rats import ci as ci
from rats import devtools as devtools

app = apps.AppBundle(app_plugin=devtools.Application)
app.get(ci.PluginServices.MAIN_CLICK)()
