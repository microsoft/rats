from rats import apps

from ._runtime import AmlRuntime


@apps.autoscope
class PluginServices:
    AML_RUNTIME = apps.ServiceId[AmlRuntime]("aml-runtime")
    HELLO_WORLD = apps.ServiceId[apps.Executable]("hello-world")


class PluginContainer(apps.Container):
    _app: apps.Container

    def __init__(self, app: apps.Container) -> None:
        self._app = app

    @apps.service(PluginServices.HELLO_WORLD)
    def _hello_world(self) -> apps.Executable:
        return apps.App(lambda: print("hello, world!"))

    @apps.service(PluginServices.AML_RUNTIME)
    def _aml_runtime(self) -> AmlRuntime:
        return AmlRuntime()
