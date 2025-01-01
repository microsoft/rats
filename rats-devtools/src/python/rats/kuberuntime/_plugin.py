import json
import logging
import os
from collections.abc import Iterator

import click

from rats import apps as apps
from rats import cli as cli
from rats import devtools as devtools
from rats import projects as projects
from rats import stdruntime as stdruntime

logger = logging.getLogger(__name__)


@apps.autoscope
class PluginServices:
    K8S_RUNTIME = apps.ServiceId[apps.Runtime]("k8s-runtime")
    COMMANDS = apps.ServiceId[cli.Container]("commands")
    MAIN_CLICK = apps.ServiceId[click.Group]("main-click")

    @staticmethod
    def component_runtime(name: str) -> apps.ServiceId[apps.Runtime]:
        return apps.ServiceId[apps.Runtime](f"{PluginServices.K8S_RUNTIME.name}[{name}][runtime]")

    @staticmethod
    def component_command(name: str) -> apps.ServiceId[tuple[str, ...]]:
        return apps.ServiceId[tuple[str, ...]](
            f"{PluginServices.K8S_RUNTIME.name}[{name}][command]",
        )


class PluginContainer(apps.Container, apps.PluginMixin, cli.Container):
    @cli.command()
    @click.option("--exe-id", multiple=True)
    @click.option("--group-id", multiple=True)
    def submit(self, exe_id: tuple[str, ...], group_id: tuple[str, ...]) -> None:
        if len(exe_id) == 0 and len(group_id) == 0:
            logger.warning("No executables or groups were passed to the command")

        tools = self._app.get(projects.PluginServices.PROJECT_TOOLS)
        cwd_component_tools = self._app.get(projects.PluginServices.CWD_COMPONENT_TOOLS)
        k8s_runtime = self._app.get(PluginServices.K8S_RUNTIME)

        tools.build_component_image(cwd_component_tools.component_name())

        exes = [apps.ServiceId[apps.Executable](exe) for exe in exe_id]
        groups = [apps.ServiceId[apps.Executable](group) for group in group_id]
        # we can join these into one job later if needed
        if len(exes):
            k8s_runtime.execute(*exes)

        if len(groups):
            k8s_runtime.execute_group(*groups)

    @cli.command()
    def worker_node(self) -> None:
        """
        Run the worker node process.

        This command is intended to be run in a k8s job. It will execute any exes and groups
        that are passed to it through environment variables.
        """
        exe_ids = json.loads(
            os.environ.get("DEVTOOLS_K8S_EXE_IDS", "[]"),
            object_hook=lambda d: apps.ServiceId[apps.Executable](**d),
        )
        group_ids = json.loads(
            os.environ.get("DEVTOOLS_K8S_EVENT_IDS", "[]"),
            object_hook=lambda d: apps.ServiceId[apps.Executable](**d),
        )

        worker_node_runtime = self._app.get(stdruntime.PluginServices.STANDARD_RUNTIME)
        worker_node_runtime.execute(*exe_ids)
        worker_node_runtime.execute_group(*group_ids)

    @apps.group(devtools.AppServices.ON_REGISTER)
    def _on_open(self) -> Iterator[apps.Executable]:
        yield apps.App(
            lambda: cli.attach(
                self._app.get(devtools.AppServices.MAIN_CLICK),
                self._app.get(PluginServices.MAIN_CLICK),
            )
        )

    @apps.service(PluginServices.MAIN_CLICK)
    def _main_click(self) -> click.Group:
        return cli.create_group(
            click.Group(
                "k8s-runtime",
                help="submit executables and events to k8s",
            ),
            self,
        )

    @apps.service(PluginServices.K8S_RUNTIME)
    def _k8s_runtime(self) -> apps.Runtime:
        ptools = self._app.get(projects.PluginServices.PROJECT_TOOLS)
        return self._app.get(PluginServices.component_runtime(ptools.devtools_component().name))
