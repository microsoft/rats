import json
import os

from rats import apps

from ._plugin import PluginServices


def run() -> None:
    app = apps.SimpleApplication(
        "rats.apps.plugins",
        "rats.devtools.plugins",
    )

    def _main() -> None:
        # need some cleanup
        if os.environ.get("K8S_RUNTIME_CTX_ID"):
            exes = json.loads(os.environ.get("K8S_RUNTIME_EXES", "[]"))
            groups = json.loads(os.environ.get("K8S_RUNTIME_EXES", "[]"))
            app.execute_group(*groups)
            app.execute(*exes)
        elif os.environ.get("FORCE_LOCAL"):
            app.execute(PluginServices.MAIN)
        else:
            k8s_runtime = app.get(PluginServices.K8S_RUNTIME)
            k8s_runtime.execute(PluginServices.MAIN)

    app.execute_callable(_main)
