"""Run the kuberuntime commands."""

from rats import apps
from rats import kuberuntime as kuberuntime

app = apps.SimpleApplication("rats.devtools.plugins")
app.execute(kuberuntime.PluginServices.MAIN_EXE)
