import os
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import final

from rats import apps

from ._command import Command


@apps.autoscope
class PluginConfigs:
    """Service IDs provided and used by [rats.cli.PluginContainer][]."""

    COMMAND = apps.ServiceId[Command]("command")
    CWD = apps.ServiceId[str]("cwd")
    ARGV = apps.ServiceId[tuple[str, ...]]("argv")
    ENV = apps.ServiceId[Mapping[str, str]]("env")


@final
class PluginContainer(apps.Container, apps.PluginMixin):
    @apps.service(PluginConfigs.COMMAND)
    def _command(self) -> Command:
        return Command(
            cwd=self._app.get(PluginConfigs.CWD),
            argv=self._app.get(PluginConfigs.ARGV),
            env=self._app.get(PluginConfigs.ENV),
        )

    @apps.fallback_service(PluginConfigs.CWD)
    def _cwd(self) -> str:
        return str(Path.cwd().resolve())

    @apps.fallback_service(PluginConfigs.ARGV)
    def _argv(self) -> tuple[str, ...]:
        return tuple(sys.argv)

    @apps.fallback_service(PluginConfigs.ENV)
    def _env(self) -> Mapping[str, str]:
        return dict(os.environ)
