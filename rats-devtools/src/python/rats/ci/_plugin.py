# pyright seems to struggle with this namespace package
# https://github.com/microsoft/pyright/issues/2882
import uuid

import click

from rats import apps as apps
from rats import cli as cli
from rats import devtools, kuberuntime

from ._commands import PluginCommands
from ._executables import PongExecutable


@apps.autoscope
class _PluginExamples:
    PONG_EXECUTABLE = apps.ServiceId[apps.Executable]("pong-executable")


@apps.autoscope
class _PluginClickServices:
    GROUP = apps.ServiceId[click.Group]("group")


@apps.autoscope
class PluginServices:
    COMMANDS = apps.ServiceId[cli.CommandContainer]("commands")
    CLICK = _PluginClickServices
    EXAMPLES = _PluginExamples


class PluginContainer(apps.Container):
    _app: apps.Container

    def __init__(self, app: apps.Container) -> None:
        self._app = app

    @apps.group(cli.PluginServices.EVENTS.command_open(cli.PluginServices.ROOT_COMMAND))
    def _on_open(self) -> apps.Executable:
        def run() -> None:
            group = self._app.get(
                cli.PluginServices.click_command(cli.PluginServices.ROOT_COMMAND)
            )
            ci = self._app.get(PluginServices.CLICK.GROUP)
            self._app.get(PluginServices.COMMANDS).on_group_open(ci)
            group.add_command(ci)

        return apps.App(run)

    @apps.service(PluginServices.COMMANDS)
    def _commands(self) -> cli.CommandContainer:
        return PluginCommands(
            project_tools=self._app.get(devtools.PluginServices.PROJECT_TOOLS),
            selected_component=self._app.get(devtools.PluginServices.ACTIVE_COMPONENT_OPS),
            devtools_component=self._app.get(devtools.PluginServices.DEVTOOLS_COMPONENT_OPS),
            # on worker nodes, we always want the simple local runtime, for now.
            worker_node_runtime=self._app.get(apps.AppServices.STANDARD_RUNTIME),
            k8s_runtime=self._app.get(kuberuntime.PluginServices.K8S_RUNTIME),
            devtools_runtime=self._app.get(
                kuberuntime.PluginServices.component_runtime("rats-devtools")
            ),
            minimal_runtime=self._app.get(
                kuberuntime.PluginServices.component_runtime("rats-examples-minimal")
            ),
        )

    @apps.service(PluginServices.CLICK.GROUP)
    def _click_group(self) -> click.Group:
        return click.Group(
            "ci",
            help="commands used during ci/cd",
        )

    @apps.service(PluginServices.EXAMPLES.PONG_EXECUTABLE)
    def _pong_executable(self) -> apps.Executable:
        return PongExecutable(f"hello from our examples: {uuid.uuid4()!s}")
