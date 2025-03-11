"""Run the docs commands."""

from rats import apps as apps
from rats import devtools as devtools
from rats import docs as docs

app = apps.AppBundle(app_plugin=devtools.Application)
app.get(docs.PluginServices.MAIN_CLICK)()
