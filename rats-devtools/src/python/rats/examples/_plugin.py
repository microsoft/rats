import uuid
from collections.abc import Iterator

from rats import amlruntime
from rats import apps as apps


@apps.autoscope
class PluginServices:
    PING = apps.ServiceId[apps.Executable]("ping")
    PONG = apps.ServiceId[apps.Executable]("pong")


class PluginContainer(apps.PluginMixin):

    @apps.fallback_group(amlruntime.PluginServices.CONFIGS.EXE_GROUP)  # type: ignore[reportArgumentType]
    def _aml_ping(self) -> Iterator[apps.Executable]:
        yield self._app.get(PluginServices.PING)

    @apps.fallback_group(amlruntime.PluginServices.CONFIGS.EXE_GROUP)  # type: ignore[reportArgumentType]
    def _aml_pong(self) -> Iterator[apps.Executable]:
        yield self._app.get(PluginServices.PONG)

    @apps.service(PluginServices.PING)
    def _ping(self) -> apps.Executable:
        return apps.App(lambda: print(f"ping: {uuid.uuid4()!s}"))

    @apps.service(PluginServices.PONG)
    def _pong(self) -> apps.Executable:
        return apps.App(lambda: print(f"pong: {uuid.uuid4()!s}"))
