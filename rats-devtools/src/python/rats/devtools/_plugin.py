import logging

from rats import apps, cli, logs

logger = logging.getLogger(__name__)


@apps.autoscope
class _PluginEvents:
    OPEN = apps.ServiceId[apps.Executable]("open")
    RUN = apps.ServiceId[apps.Executable]("run")
    CLOSE = apps.ServiceId[apps.Executable]("close")

    @staticmethod
    def app_open(app: apps.ServiceId[apps.Executable]) -> apps.ServiceId[apps.Executable]:
        return apps.ServiceId(f"{app.name}[open]")

    @staticmethod
    def app_run(app: apps.ServiceId[apps.Executable]) -> apps.ServiceId[apps.Executable]:
        return apps.ServiceId(f"{app.name}[run]")

    @staticmethod
    def app_close(app: apps.ServiceId[apps.Executable]) -> apps.ServiceId[apps.Executable]:
        return apps.ServiceId(f"{app.name}[close]")


@apps.autoscope
class PluginServices:
    MAIN = apps.ServiceId[apps.Executable]("main")
    EVENTS = _PluginEvents


class PluginContainer(apps.Container):
    _app: apps.Container

    def __init__(self, app: apps.Container) -> None:
        self._app = app

    @apps.service(PluginServices.MAIN)
    def _main(self) -> apps.Executable:
        runtime = self._app.get(apps.AppServices.RUNTIME)
        return apps.App(
            lambda: runtime.execute_group(
                logs.PluginServices.EVENTS.CONFIGURE_LOGGING,
                PluginServices.EVENTS.app_open(PluginServices.MAIN),
                PluginServices.EVENTS.app_run(PluginServices.MAIN),
                PluginServices.EVENTS.app_close(PluginServices.MAIN),
            )
        )

    @apps.group(PluginServices.EVENTS.app_open(PluginServices.MAIN))
    def _on_app_open(self) -> apps.Executable:
        return apps.App(lambda: logger.debug("Opening app"))

    @apps.group(PluginServices.EVENTS.app_run(PluginServices.MAIN))
    def _on_app_run(self) -> apps.Executable:
        # our main app here runs a cli command, but it can also directly do something useful
        return self._app.get(cli.PluginServices.ROOT_COMMAND)

    @apps.group(PluginServices.EVENTS.app_close(PluginServices.MAIN))
    def _on_app_close(self) -> apps.Executable:
        return apps.App(lambda: logger.debug("Closing app"))
