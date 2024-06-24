from typing import cast, final

import click

from rats import apps


@apps.autoscope
class _PluginEvents:
    @staticmethod
    def command_open(cmd_id: apps.ServiceId[apps.Executable]) -> apps.ServiceId[apps.Executable]:
        return apps.ServiceId(f"command-open[{cmd_id.name}]")

    @staticmethod
    def command_execute(
        cmd_id: apps.ServiceId[apps.Executable],
    ) -> apps.ServiceId[apps.Executable]:
        return apps.ServiceId(f"command-execute[{cmd_id.name}]")

    @staticmethod
    def command_close(cmd_id: apps.ServiceId[apps.Executable]) -> apps.ServiceId[apps.Executable]:
        return apps.ServiceId(f"command-close[{cmd_id.name}]")


@apps.autoscope
class PluginServices:
    ROOT_COMMAND = apps.ServiceId[apps.Executable]("root-command")
    EVENTS = _PluginEvents

    @staticmethod
    def sub_command(
        parent: apps.ServiceId[apps.Executable],
        name: str,
    ) -> apps.ServiceId[apps.Executable]:
        return apps.ServiceId(f"{parent.name}[{name}]")

    @staticmethod
    def click_command(cmd_id: apps.ServiceId[apps.Executable]) -> apps.ServiceId[click.Group]:
        # autowrapped!
        return cast(apps.ServiceId[click.Group], cmd_id)


@final
class PluginContainer(apps.Container):
    _app: apps.Container

    def __init__(self, app: apps.Container) -> None:
        self._app = app

    @apps.service(PluginServices.ROOT_COMMAND)
    def _root_command(self) -> apps.Executable:
        def run() -> None:
            runtime = self._app.get(apps.AppServices.RUNTIME)
            runtime.execute_group(
                PluginServices.EVENTS.command_open(PluginServices.ROOT_COMMAND),
                PluginServices.EVENTS.command_execute(PluginServices.ROOT_COMMAND),
                PluginServices.EVENTS.command_close(PluginServices.ROOT_COMMAND),
            )

        return apps.App(run)

    @apps.fallback_group(PluginServices.EVENTS.command_execute(PluginServices.ROOT_COMMAND))
    def _default_command(self) -> apps.Executable:
        group = self._app.get(PluginServices.click_command(PluginServices.ROOT_COMMAND))
        return apps.App(lambda: group())

    @apps.service(PluginServices.click_command(PluginServices.ROOT_COMMAND))
    def _root_click_command(self) -> click.Group:
        return click.Group("groot")
