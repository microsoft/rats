import logging

from rats import apps, cli, logs

logger = logging.getLogger(__name__)


@apps.autoscope
class _PluginEvents:
    OPENING = apps.ServiceId[apps.Executable]("opening")
    RUNNING = apps.ServiceId[apps.Executable]("running")
    CLOSING = apps.ServiceId[apps.Executable]("closing")


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
                PluginServices.EVENTS.OPENING,
                PluginServices.EVENTS.RUNNING,
                PluginServices.EVENTS.CLOSING,
            )
        )

    @apps.group(PluginServices.EVENTS.OPENING)
    def _on_opening(self) -> apps.Executable:
        return apps.App(lambda: logger.debug("Opening app"))

    @apps.group(PluginServices.EVENTS.RUNNING)
    def _on_running(self) -> apps.Executable:
        # our main app here runs a cli command, but it can also directly do something useful
        return self._app.get(cli.PluginServices.ROOT_COMMAND)

    @apps.group(PluginServices.EVENTS.CLOSING)
    def _on_closing(self) -> apps.Executable:
        return apps.App(lambda: logger.debug("Closing app"))
