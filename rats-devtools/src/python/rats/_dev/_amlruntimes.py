from rats import apps, amlruntime


class AmlRuntimePluginContainer(apps.Container):
    _app: apps.Container

    def __init__(self, app: apps.Container) -> None:
        self._app = app

    @apps.service(amlruntime.PluginServices.component_runtime("rats-devtools"))
    def _devtools_runtime(self) -> amlruntime.AmlRuntime:
        return amlruntime.AmlRuntime(
            ml_client=lambda: self._app.get(amlruntime.PluginServices.AML_CLIENT),
            environment_operations=lambda: self._app.get(
                amlruntime.PluginServices.AML_ENVIRONMENT_OPS,
            ),
            job_operations=lambda: self._app.get(amlruntime.PluginServices.AML_JOB_OPS),
            config=lambda: self._app.get(amlruntime.PluginServices.CONFIGS.component_runtime(
                "rats-devtools",
            )),
        )
