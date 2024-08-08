import uuid

import click

from rats import apps as apps
from rats import cli as cli
from rats import devtools, kuberuntime, projects

from ._commands import PluginCommands
from ._executables import PingExecutable, PongExecutable


@apps.autoscope
class _PluginExamples:
    PING_EXECUTABLE = apps.ServiceId[apps.Executable]("ping-executable")
    PONG_EXECUTABLE = apps.ServiceId[apps.Executable]("pong-executable")


@apps.autoscope
class PluginServices:
    COMMANDS = apps.ServiceId[cli.CommandContainer]("commands")
    MAIN_EXE = apps.ServiceId[apps.Executable]("main-exe")
    MAIN_CLICK = apps.ServiceId[click.Group]("main-click")
    EXAMPLES = _PluginExamples


class PluginContainer(apps.Container):
    _app: apps.Container

    def __init__(self, app: apps.Container) -> None:
        self._app = app

    @apps.group(devtools.PluginServices.EVENTS.OPENING)
    def _on_open(self) -> apps.Executable:
        def run() -> None:
            parent = self._app.get(devtools.PluginServices.MAIN_CLICK)
            ci = self._app.get(PluginServices.MAIN_CLICK)
            self._app.get(PluginServices.COMMANDS).attach(ci)
            parent.add_command(ci)

        return apps.App(run)

    @apps.service(PluginServices.COMMANDS)
    def _commands(self) -> cli.CommandContainer:
        return PluginCommands(
            project_tools=self._app.get(projects.PluginServices.PROJECT_TOOLS),
            selected_component=self._app.get(projects.PluginServices.ACTIVE_COMPONENT_OPS),
            devtools_component=self._app.get(projects.PluginServices.DEVTOOLS_COMPONENT_OPS),
            ping=self._app.get(PluginServices.EXAMPLES.PING_EXECUTABLE),
            pong=self._app.get(PluginServices.EXAMPLES.PONG_EXECUTABLE),
            standard_runtime=self._app.get(apps.AppServices.STANDARD_RUNTIME),
            k8s_runtime=self._app.get(kuberuntime.PluginServices.K8S_RUNTIME),
            devtools_runtime=self._app.get(
                kuberuntime.PluginServices.component_runtime("rats-devtools")
            ),
            minimal_runtime=self._app.get(
                kuberuntime.PluginServices.component_runtime("rats-examples-minimal")
            ),
        )

    @apps.service(PluginServices.MAIN_EXE)
    def _main_exe(self) -> apps.Executable:
        return apps.App(lambda: self._app.get(PluginServices.MAIN_CLICK)())

    @apps.service(PluginServices.MAIN_CLICK)
    def _main_click(self) -> click.Group:
        command_container = self._app.get(PluginServices.COMMANDS)
        ci = click.Group(
            "ci",
            help="commands used during ci/cd",
        )
        command_container.attach(ci)
        return ci

    @apps.service(PluginServices.EXAMPLES.PONG_EXECUTABLE)
    def _pong_executable(self) -> apps.Executable:
        return PongExecutable(f"hello from our examples: {uuid.uuid4()!s}")

    @apps.service(PluginServices.EXAMPLES.PING_EXECUTABLE)
    def _ping_executable(self) -> apps.Executable:
        return PingExecutable(f"hello from our examples: {uuid.uuid4()!s}")
