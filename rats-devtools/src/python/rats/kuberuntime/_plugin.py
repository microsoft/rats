from collections.abc import Iterator
from typing import cast

import click

from rats import apps, cli
from rats import devtools as devtools
from rats import projects as projects

from ._commands import PluginCommands


@apps.autoscope
class PluginServices:
    K8S_RUNTIME = apps.ServiceId[apps.Runtime]("k8s-runtime")
    COMMANDS = apps.ServiceId[cli.CommandContainer]("commands")
    MAIN_EXE = apps.ServiceId[apps.Executable]("main-exe")
    MAIN_CLICK = apps.ServiceId[click.Group]("main-click")

    @staticmethod
    def component_runtime(name: str) -> apps.ServiceId[apps.Runtime]:
        return apps.ServiceId[apps.Runtime](f"{PluginServices.K8S_RUNTIME.name}[{name}][runtime]")

    @staticmethod
    def component_command(name: str) -> apps.ServiceId[tuple[str, ...]]:
        return apps.ServiceId[tuple[str, ...]](
            f"{PluginServices.K8S_RUNTIME.name}[{name}][command]",
        )


class PluginContainer(apps.Container):
    _app: apps.Container

    def __init__(self, app: apps.Container) -> None:
        self._app = app

    @apps.group(devtools.PluginServices.EVENTS.OPENING)
    def _runner_cli(self) -> Iterator[apps.Executable]:
        def run() -> None:
            kuberuntime = self._app.get(PluginServices.MAIN_CLICK)
            parent = self._app.get(devtools.PluginServices.MAIN_CLICK)
            self._app.get(PluginServices.COMMANDS).attach(kuberuntime)
            parent.add_command(cast(click.Command, kuberuntime))

        yield apps.App(run)

    @apps.service(PluginServices.MAIN_EXE)
    def _main_exe(self) -> apps.Executable:
        return apps.App(lambda: self._app.get(PluginServices.MAIN_CLICK)())

    @apps.service(PluginServices.MAIN_CLICK)
    def _main_click(self) -> click.Group:
        command_container = self._app.get(PluginServices.COMMANDS)
        kuberuntime = click.Group(
            "k8s-runtime",
            help="submit executables and events to k8s",
        )
        command_container.attach(kuberuntime)
        return kuberuntime

    @apps.service(PluginServices.COMMANDS)
    def _commands(self) -> cli.CommandContainer:
        return PluginCommands(
            project_tools=lambda: self._app.get(projects.PluginServices.PROJECT_TOOLS),
            cwd_component_tools=lambda: self._app.get(projects.PluginServices.CWD_COMPONENT_TOOLS),
            # on worker nodes, we always want the simple local runtime, for now.
            worker_node_runtime=lambda: self._app.get(apps.AppServices.STANDARD_RUNTIME),
            k8s_runtime=lambda: self._app.get(PluginServices.K8S_RUNTIME),
        )

    @apps.service(PluginServices.K8S_RUNTIME)
    def _k8s_runtime(self) -> apps.Runtime:
        ptools = self._app.get(projects.PluginServices.PROJECT_TOOLS)
        return self._app.get(PluginServices.component_runtime(ptools.devtools_component().name))
