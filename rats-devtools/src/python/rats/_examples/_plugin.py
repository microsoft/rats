import uuid

from rats import apps


@apps.autoscope
class ExamplesPluginServices:
    PING = apps.ServiceId[apps.Executable]("ping")
    PONG = apps.ServiceId[apps.Executable]("pong")


class ExamplesPluginContainer(apps.Container):
    _app: apps.Container

    def __init__(self, app: apps.Container) -> None:
        self._app = app

    @apps.service(ExamplesPluginServices.PING)
    def _ping(self) -> apps.Executable:
        return apps.App(lambda: print(f"ping: {str(uuid.uuid4())}"))

    @apps.service(ExamplesPluginServices.PONG)
    def _pong(self) -> apps.Executable:
        return apps.App(lambda: print(f"pong: {str(uuid.uuid4())}"))
