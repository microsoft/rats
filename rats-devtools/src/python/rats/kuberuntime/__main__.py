"""Run the kuberuntime commands."""

from rats import apps
from rats import devtools as devtools
from rats import kuberuntime as kuberuntime

app = apps.AppBundle(app_plugin=devtools.Application)
app.get(kuberuntime.PluginServices.MAIN_CLICK)()
