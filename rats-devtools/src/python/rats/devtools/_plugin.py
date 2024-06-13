# pyright seems to struggle with this namespace package
# https://github.com/microsoft/pyright/issues/2882
from rats import apps as apps, logs


import logging

logger = logging.getLogger(__name__)


@apps.autoscope
class _PluginEvents:
    APP_OPEN = apps.ServiceId[apps.Executable]("app-open")
    APP_RUN = apps.ServiceId[apps.Executable]("app-run")
    APP_CLOSE = apps.ServiceId[apps.Executable]("app-close")


@apps.autoscope
class PluginServices:
    MAIN = apps.ServiceId[apps.Executable]("main")
    EVENTS = _PluginEvents


class PluginContainer(apps.Container):
    _app: apps.Container

    def __init__(self, app: apps.Container) -> None:
        self._app = app

    @apps.service(PluginServices.MAIN)
    def main(self) -> apps.Executable:
        runtime = self._app.get(apps.AppServices.RUNTIME)
        return apps.App(
            lambda: runtime.execute_group(
                logs.PluginServices.EVENTS.CONFIGURE_LOGGING,
                PluginServices.EVENTS.APP_OPEN,
                PluginServices.EVENTS.APP_RUN,
                PluginServices.EVENTS.APP_CLOSE,
            )
        )

    @apps.group(PluginServices.EVENTS.APP_OPEN)
    def on_app_open(self) -> apps.Executable:
        return apps.App(lambda: logger.info("Opening app"))

    @apps.group(PluginServices.EVENTS.APP_RUN)
    def on_app_run(self) -> apps.Executable:
        return apps.App(lambda: logger.info("Running app"))

    @apps.group(PluginServices.EVENTS.APP_CLOSE)
    def on_app_close(self) -> apps.Executable:
        return apps.App(lambda: logger.info("Closing app"))
