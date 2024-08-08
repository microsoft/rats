from typing import cast, final

import click

from rats import apps


@apps.autoscope
class _PluginEvents:
    pass


@apps.autoscope
class PluginServices:
    EVENTS = _PluginEvents

    @staticmethod
    def sub_command(
        parent: apps.ServiceId[apps.Executable],
        name: str,
    ) -> apps.ServiceId[apps.Executable]:
        return apps.ServiceId(f"{parent.name}[{name}]")

    @staticmethod
    def click_command(cmd_id: apps.ServiceId[apps.Executable]) -> apps.ServiceId[click.Group]:
        return cast(apps.ServiceId[click.Group], cmd_id)


@final
class PluginContainer(apps.Container):
    _app: apps.Container

    def __init__(self, app: apps.Container) -> None:
        self._app = app
