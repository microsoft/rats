import uuid

from rats import amlruntime
from rats import apps as apps


@apps.autoscope
class PluginServices:
    PING = apps.ServiceId[apps.Executable]("ping")
    PONG = apps.ServiceId[apps.Executable]("pong")


class PluginContainer(apps.Container):
    _app: apps.Container

    def __init__(self, app: apps.Container) -> None:
        self._app = app

    @apps.fallback_group(amlruntime.PluginServices.CONFIGS.EXE_GROUP)  # type: ignore[reportArgumentType]
    def _aml_ping(self) -> apps.Executable:
        return self._app.get(PluginServices.PING)

    @apps.fallback_group(amlruntime.PluginServices.CONFIGS.EXE_GROUP)  # type: ignore[reportArgumentType]
    def _aml_pong(self) -> apps.Executable:
        return self._app.get(PluginServices.PONG)

    @apps.service(PluginServices.PING)
    def _ping(self) -> apps.Executable:
        return apps.App(lambda: print(f"ping: {uuid.uuid4()!s}"))

    @apps.service(PluginServices.PONG)
    def _pong(self) -> apps.Executable:
        return apps.App(lambda: print(f"pong: {uuid.uuid4()!s}"))
