import logging
from collections.abc import Iterator

import click

from rats import apps, cli, logs
from rats import projects as projects


logger = logging.getLogger(__name__)


@apps.autoscope
class _PluginEvents:
    OPENING = apps.ServiceId[apps.Executable]("opening")
    RUNNING = apps.ServiceId[apps.Executable]("running")
    CLOSING = apps.ServiceId[apps.Executable]("closing")


@apps.autoscope
class PluginServices:
    MAIN_EXE = apps.ServiceId[apps.Executable]("main-exe")
    MAIN_CLICK = apps.ServiceId[click.Group]("main-click")
    COMMANDS = apps.ServiceId[cli.Container]("commands")
    EVENTS = _PluginEvents
